from pydantic import BaseModel
from app.models.domain import Candidate, ProfileRecord


class AddCandidateRequest(BaseModel):
    candidate: Candidate


class ResolveRequest(BaseModel):
    query: ProfileRecord


class DiscoveryRequest(BaseModel):
    name: str
    username: str | None = None


class ExtractRequest(BaseModel):
    profiles: list[ProfileRecord]
