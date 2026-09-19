from pydantic import BaseModel
from app.models.domain import Candidate, ProfileRecord


class AddCandidateRequest(BaseModel):
    candidate: Candidate


class ResolveRequest(BaseModel):
    query: ProfileRecord
