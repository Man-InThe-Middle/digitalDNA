from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class SourceType(str, Enum):
    SEARCH = "search"
    SOCIAL = "social"
    PROFESSIONAL = "professional"
    CODE = "code"
    EVENT = "event"
    WEBSITE = "website"
    PUBLICATION = "publication"
    OTHER = "other"


class ResolutionStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PROBABLE = "PROBABLE"
    POSSIBLE = "POSSIBLE"
    CONFLICT = "CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class InvestigationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_label: str = Field(min_length=1, max_length=200)
    context: str | None = Field(default=None, max_length=5000)
    authorized: bool = False
    image_sha256: str | None = None


class Investigation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    subject_label: str
    context: str | None = None
    authorized: bool
    image_sha256: str | None = None
    created_at: datetime = Field(default_factory=now_utc)


class ProfileRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    platform: str
    username: str | None = None
    display_name: str | None = None
    url: HttpUrl | None = None
    bio: str | None = None
    organization: str | None = None
    location: str | None = None
    source_type: SourceType = SourceType.OTHER
    discovered_at: datetime = Field(default_factory=now_utc)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_url: HttpUrl | None = None
    source_type: SourceType = SourceType.OTHER
    claim: str = Field(min_length=1)
    excerpt: str | None = None
    signal_type: str = Field(min_length=1)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    reliability: float = Field(default=0.5, ge=0.0, le=1.0)
    observed_at: datetime = Field(default_factory=now_utc)


class Candidate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    profiles: list[ProfileRecord] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class ResolutionResult(BaseModel):
    candidate_id: UUID
    score: float = Field(ge=0.0, le=100.0)
    status: ResolutionStatus
    signals: dict[str, float]
    supporting_evidence: list[UUID] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class Relationship(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_entity: str
    relationship: str
    target_entity: str
    evidence_ids: list[UUID] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class GraphResponse(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[Relationship]
