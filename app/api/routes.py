from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from app.config import settings
from app.core.pipeline import run_pipeline
from app.core.analysis.ollama import OllamaAnalyzer
from app.db.store import store
from app.models.domain import Investigation

router = APIRouter(prefix="/api/v1")
UPLOAD_DIR = Path("investigations")
UPLOAD_DIR.mkdir(exist_ok=True)


def _record(inv_id):
    row = store.get(inv_id)
    if not row:
        raise HTTPException(404, "Investigation not found.")
    return row


def _public(inv, status, result):
    out = {"investigation": inv.model_dump(mode="json"), "status": status}
    if result:
        out.update(result)
    return out


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "DigitalDNA",
        "version": "2.1",
        "persistence": "sqlite",
        "public_sources_only": settings.public_sources_only,
        "entity_store": True,
    }


@router.get("/providers")
async def providers():
    return {"providers": [
        {"name": "github", "kind": "public_api", "enabled": True},
        {"name": "web_search", "kind": "public_search", "enabled": settings.enable_web_search},
        {"name": "website_enrichment", "kind": "public_page_fetch", "enabled": settings.enable_web_search},
        {"name": "ollama_local", "kind": "local_llm", "enabled": settings.enable_ollama},
    ]}


@router.get("/investigations")
async def list_investigations(limit: int = 20):
    return {"items": store.list_recent(max(1, min(limit, 100)))}


@router.post("/investigations", status_code=201)
async def create_investigation(
    subject_label: str = Form(...),
    context: str = Form(""),
    authorized: bool = Form(False),
    discovery_mode: str = Form("demo"),
    image: UploadFile | None = File(None),
):
    if settings.require_authorization and not authorized:
        raise HTTPException(403, "Explicit authorization is required.")
    subject_label = subject_label.strip()
    discovery_mode = discovery_mode.strip().lower()
    if not subject_label:
        raise HTTPException(422, "Subject label cannot be empty.")
    if discovery_mode not in {"demo", "live", "hybrid"}:
        raise HTTPException(422, "Discovery mode must be demo, live, or hybrid.")

    sha = name = None
    if image:
        if not (image.content_type or "").startswith("image/"):
            raise HTTPException(415, "Only image uploads are accepted.")
        data = await image.read()
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, "Image exceeds upload limit.")
        sha = hashlib.sha256(data).hexdigest()
        name = Path(image.filename or "authorized-image").name
        (UPLOAD_DIR / f"{sha}_{name}").write_bytes(data)

    inv = Investigation(
        subject_label=subject_label,
        context=context.strip() or None,
        authorized=authorized,
        discovery_mode=discovery_mode,
        image_sha256=sha,
        image_name=name,
    )
    store.save_investigation(inv)
    return inv


@router.post("/investigations/{investigation_id}/run")
async def run_investigation(investigation_id: UUID):
    inv, _, _ = _record(investigation_id)
    if not inv.authorized:
        raise HTTPException(403, "Investigation is not authorized.")
    try:
        store.set_status(investigation_id, "running")
        result = await run_pipeline(inv)
        store.set_result(investigation_id, result)
        # Dedicated normalized persistence. result_json remains the portable snapshot.
        from app.models.domain import Entity, EntityRelationship
        entities = [Entity.model_validate(x) for x in result.get("entities", [])]
        relationships = [EntityRelationship.model_validate(x) for x in result.get("entity_relationships", [])]
        store.replace_entity_graph(investigation_id, entities, relationships)
    except Exception as exc:
        store.set_status(investigation_id, "failed")
        raise HTTPException(502, f"Investigation pipeline failed: {type(exc).__name__}: {exc}") from exc
    return _public(inv, "complete", result)


@router.post("/investigations/{investigation_id}/analyze")
async def analyze_investigation(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    if not inv.authorized:
        raise HTTPException(403, "Investigation is not authorized.")
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    if not settings.enable_ollama:
        raise HTTPException(503, "Local Ollama analysis is disabled. Set ENABLE_OLLAMA=true.")
    try:
        from app.models.domain import Candidate, Evidence
        candidate = Candidate.model_validate(result["candidate"])
        evidence = [Evidence.model_validate(e) for e in result.get("evidence", [])]
        analysis = await OllamaAnalyzer(
            settings.ollama_url, settings.ollama_model, settings.ollama_timeout
        ).analyze(inv.subject_label, candidate, evidence)
        result["ai_analysis"] = analysis
        store.set_result(investigation_id, result)
        return _public(inv, status, result)
    except Exception as exc:
        raise HTTPException(502, f"Local analysis failed: {type(exc).__name__}: {exc}") from exc


@router.get("/investigations/{investigation_id}")
async def get_investigation(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    return _public(inv, status, result)


@router.get("/investigations/{investigation_id}/candidates")
async def candidates(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    return {
        "investigation_id": str(inv.id),
        "primary": result["candidate"],
        "resolution": result["resolution"],
        "alternates": result.get("alternates", []),
    }


@router.get("/investigations/{investigation_id}/entities")
async def entities(investigation_id: UUID, entity_type: str | None = None):
    inv, status, result = _record(investigation_id)
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    items, _ = store.get_entity_graph(investigation_id)
    if entity_type:
        wanted = entity_type.strip().upper()
        items = [x for x in items if x["type"] == wanted]
    return {"investigation_id": str(inv.id), "count": len(items), "entities": items}


@router.get("/investigations/{investigation_id}/relationships")
async def entity_relationships(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    _, relationships = store.get_entity_graph(investigation_id)
    return {"investigation_id": str(inv.id), "count": len(relationships), "relationships": relationships}


@router.get("/investigations/{investigation_id}/entity-graph")
async def entity_graph(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    entities, relationships = store.get_entity_graph(investigation_id)
    return {
        "investigation_id": str(inv.id),
        "nodes": entities,
        "edges": relationships,
        "counts": {
            "entities": len(entities),
            "relationships": len(relationships),
            "people": sum(x["type"] == "PERSON" for x in entities),
            "accounts": sum(x["type"] == "ACCOUNT" for x in entities),
            "organizations": sum(x["type"] == "ORGANIZATION" for x in entities),
            "projects": sum(x["type"] == "PROJECT" for x in entities),
            "events": sum(x["type"] == "EVENT" for x in entities),
            "publications": sum(x["type"] == "PUBLICATION" for x in entities),
            "aliases": sum(x["type"] == "ALIAS" for x in entities),
        },
    }


@router.get("/investigations/{investigation_id}/graph")
async def graph(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    return {"investigation_id": str(inv.id), "graph": result["graph"]}


@router.get("/investigations/{investigation_id}/evidence")
async def evidence(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    return {"investigation_id": str(inv.id), "evidence": result.get("evidence", [])}


@router.get("/investigations/{investigation_id}/timeline")
async def timeline(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    return {"investigation_id": str(inv.id), "timeline": result["timeline"]}


@router.get("/investigations/{investigation_id}/report")
async def report(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    return _public(inv, status, result)


@router.get("/investigations/{investigation_id}/report.html", response_class=HTMLResponse)
async def report_html(investigation_id: UUID):
    inv, status, result = _record(investigation_id)
    if not result:
        raise HTTPException(409, "Run the investigation first.")
    payload = html.escape(json.dumps(result, indent=2, default=str))
    return HTMLResponse(f"<html><body><h1>DigitalDNA Report</h1><pre>{payload}</pre></body></html>")
