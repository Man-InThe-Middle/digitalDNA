from uuid import UUID
from fastapi import APIRouter, HTTPException

from app.api.schemas import AddCandidateRequest, ResolveRequest
from app.models.domain import Investigation, InvestigationCreate, Candidate
from app.core.resolution.resolver import rank_candidates
from app.core.graph.builder import build_graph

router = APIRouter(prefix="/api/v1")

INVESTIGATIONS: dict[UUID, Investigation] = {}
CANDIDATES: dict[UUID, list[Candidate]] = {}


@router.post("/investigations", response_model=Investigation, status_code=201)
async def create_investigation(payload: InvestigationCreate):
    if not payload.authorized:
        raise HTTPException(status_code=403, detail="Explicit authorization is required.")
    investigation = Investigation(**payload.model_dump())
    INVESTIGATIONS[investigation.id] = investigation
    CANDIDATES[investigation.id] = []
    return investigation


@router.get("/investigations/{investigation_id}", response_model=Investigation)
async def get_investigation(investigation_id: UUID):
    investigation = INVESTIGATIONS.get(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return investigation


@router.post("/investigations/{investigation_id}/candidates", response_model=Candidate, status_code=201)
async def add_candidate(investigation_id: UUID, payload: AddCandidateRequest):
    if investigation_id not in INVESTIGATIONS:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    CANDIDATES[investigation_id].append(payload.candidate)
    return payload.candidate


@router.post("/investigations/{investigation_id}/resolve")
async def resolve(investigation_id: UUID, payload: ResolveRequest):
    if investigation_id not in INVESTIGATIONS:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return {"results": rank_candidates(payload.query, CANDIDATES[investigation_id])}


@router.get("/investigations/{investigation_id}/graph")
async def graph(investigation_id: UUID):
    if investigation_id not in INVESTIGATIONS:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return build_graph(CANDIDATES[investigation_id])
