from __future__ import annotations
from datetime import datetime
from typing import Any
from urllib.parse import urlparse
from app.models.domain import (
    Candidate, Entity, EntityRelation, EntityRelationship, EntityType, Evidence, ProfileRecord,
)


def _norm(value: str | None) -> str:
    return "".join(ch.lower() for ch in (value or "") if ch.isalnum())


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:500] if text else None


def _url(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    if text.startswith(("http://", "https://")):
        return text
    return None


def _entity_key(entity_type: EntityType, label: str, url: str | None = None) -> tuple[str, str]:
    identity = url.rstrip("/").casefold() if url else _norm(label)
    return entity_type.value, identity


def _evidence_for_profile(evidence: list[Evidence], profile_id) -> list[Evidence]:
    return [e for e in evidence if profile_id in e.profile_ids]


def _confidence(items: list[Evidence], floor: float = 0.35) -> float:
    if not items:
        return floor
    return round(max(floor, min(0.99, max(e.reliability * e.weight for e in items))), 3)


def _add_entity(
    entities: dict[tuple[str, str], Entity],
    entity_type: EntityType,
    label: str,
    *,
    url: str | None = None,
    aliases: list[str] | None = None,
    source_ids: list = None,
    evidence_ids: list = None,
    confidence: float = 0.5,
    metadata: dict[str, Any] | None = None,
) -> Entity:
    key = _entity_key(entity_type, label, url)
    if key in entities:
        existing = entities[key]
        existing.aliases = sorted(set(existing.aliases + (aliases or [])))
        existing.source_ids = list(dict.fromkeys(existing.source_ids + (source_ids or [])))
        existing.evidence_ids = list(dict.fromkeys(existing.evidence_ids + (evidence_ids or [])))
        existing.confidence = max(existing.confidence, confidence)
        existing.metadata.update(metadata or {})
        return existing
    entity = Entity(
        type=entity_type,
        label=label,
        canonical_url=url,
        aliases=sorted(set(aliases or [])),
        source_ids=list(dict.fromkeys(source_ids or [])),
        evidence_ids=list(dict.fromkeys(evidence_ids or [])),
        confidence=confidence,
        metadata=metadata or {},
    )
    entities[key] = entity
    return entity


def _add_relation(
    relationships: dict[tuple[str, str, str], EntityRelationship],
    source: Entity,
    target: Entity,
    relation: EntityRelation,
    evidence: list[Evidence],
    source_ids: list,
    confidence: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    key = (str(source.id), relation.value, str(target.id))
    ids = [e.id for e in evidence]
    if key in relationships:
        r = relationships[key]
        r.evidence_ids = list(dict.fromkeys(r.evidence_ids + ids))
        r.source_ids = list(dict.fromkeys(r.source_ids + source_ids))
        r.confidence = max(r.confidence, confidence)
        r.metadata.update(metadata or {})
        return
    relationships[key] = EntityRelationship(
        from_entity_id=source.id,
        to_entity_id=target.id,
        relation_type=relation,
        evidence_ids=list(dict.fromkeys(ids)),
        source_ids=list(dict.fromkeys(source_ids)),
        confidence=confidence,
        metadata=metadata or {},
    )


def _iter_records(value: Any):
    if isinstance(value, dict):
        yield value
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                yield item


def extract_entity_graph(candidate: Candidate, evidence: list[Evidence]) -> tuple[list[Entity], list[EntityRelationship]]:
    """Turn source profiles into first-class entities and evidence-backed edges.

    This is deliberately deterministic. LLMs are not used to invent entities;
    every emitted entity/edge can be traced to a profile and/or evidence item.
    """
    entities: dict[tuple[str, str], Entity] = {}
    relationships: dict[tuple[str, str, str], EntityRelationship] = {}

    person = _add_entity(
        entities, EntityType.PERSON, candidate.name,
        evidence_ids=[e.id for e in evidence],
        confidence=0.5,
        metadata={"role": "investigation_subject"},
    )

    for profile in candidate.profiles:
        pe = _evidence_for_profile(evidence, profile.id)
        account_label = profile.username or profile.display_name or profile.platform
        account = _add_entity(
            entities, EntityType.ACCOUNT, account_label,
            url=str(profile.url) if profile.url else None,
            aliases=[profile.display_name] if profile.display_name and profile.display_name != account_label else [],
            source_ids=[profile.id], evidence_ids=[e.id for e in pe],
            confidence=_confidence(pe, 0.45),
            metadata={"platform": profile.platform, "source_type": profile.source_type.value, "username": profile.username},
        )
        _add_relation(relationships, person, account, EntityRelation.HAS_ACCOUNT, pe, [profile.id], _confidence(pe, 0.45))

        if profile.username:
            alias = _add_entity(
                entities, EntityType.ALIAS, f"@{profile.username}",
                aliases=[profile.username], source_ids=[profile.id], evidence_ids=[e.id for e in pe],
                confidence=_confidence(pe, 0.45), metadata={"platform": profile.platform},
            )
            _add_relation(relationships, alias, person, EntityRelation.ALIAS_OF, pe, [profile.id], _confidence(pe, 0.45))

        if profile.organization:
            org = _add_entity(
                entities, EntityType.ORGANIZATION, profile.organization,
                source_ids=[profile.id], evidence_ids=[e.id for e in pe],
                confidence=_confidence([e for e in pe if e.signal_type == "organization_overlap"], 0.4),
                metadata={"observed_via": profile.platform},
            )
            _add_relation(relationships, person, org, EntityRelation.AFFILIATED_WITH, pe, [profile.id], _confidence(pe, 0.4), {"field": "organization"})

        for repo in profile.metadata.get("repo_details", []) if isinstance(profile.metadata.get("repo_details"), list) else []:
            label = _clean(repo.get("name"))
            if not label:
                continue
            project = _add_entity(
                entities, EntityType.PROJECT, label,
                url=_url(repo.get("url")), source_ids=[profile.id], evidence_ids=[e.id for e in pe if e.signal_type == "project_activity"],
                confidence=_confidence([e for e in pe if e.signal_type == "project_activity"], 0.5),
                metadata={"description": repo.get("description"), "updated_at": repo.get("updated_at"), "platform": profile.platform},
            )
            proj_ev = [e for e in pe if e.signal_type == "project_activity"]
            _add_relation(relationships, person, project, EntityRelation.CONTRIBUTES_TO, proj_ev or pe, [profile.id], _confidence(proj_ev, 0.45))

        for record in _iter_records(profile.metadata.get("events")):
            label = _clean(record.get("name") or record.get("title"))
            if not label:
                continue
            event = _add_entity(
                entities, EntityType.EVENT, label,
                url=_url(record.get("url")), source_ids=[profile.id], evidence_ids=[e.id for e in pe],
                confidence=_confidence(pe, 0.4),
                metadata={k: record.get(k) for k in ("date", "location", "organizer", "role") if record.get(k) is not None},
            )
            _add_relation(relationships, person, event, EntityRelation.PARTICIPATED_IN, pe, [profile.id], _confidence(pe, 0.4))

        for record in _iter_records(profile.metadata.get("publications")):
            label = _clean(record.get("title") or record.get("name"))
            if not label:
                continue
            pub = _add_entity(
                entities, EntityType.PUBLICATION, label,
                url=_url(record.get("url")), source_ids=[profile.id], evidence_ids=[e.id for e in pe],
                confidence=_confidence(pe, 0.4),
                metadata={k: record.get(k) for k in ("date", "venue", "type") if record.get(k) is not None},
            )
            _add_relation(relationships, person, pub, EntityRelation.AUTHORED, pe, [profile.id], _confidence(pe, 0.4))

        for link in profile.metadata.get("outbound_public_links", []) if isinstance(profile.metadata.get("outbound_public_links"), list) else []:
            if not isinstance(link, str) or not link.startswith(("http://", "https://")):
                continue
            parsed = urlparse(link)
            host = parsed.netloc.lower().removeprefix("www.")
            if not host:
                continue
            linked = _add_entity(
                entities, EntityType.ACCOUNT, host,
                url=link, source_ids=[profile.id], evidence_ids=[e.id for e in pe if e.signal_type == "explicit_cross_link"],
                confidence=_confidence([e for e in pe if e.signal_type == "explicit_cross_link"], 0.5),
                metadata={"platform_hint": host},
            )
            link_ev = [e for e in pe if e.signal_type == "explicit_cross_link"]
            _add_relation(relationships, account, linked, EntityRelation.LINKS_TO, link_ev or pe, [profile.id], _confidence(link_ev, 0.5))

    return list(entities.values()), list(relationships.values())
