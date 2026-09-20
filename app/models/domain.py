from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


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


class ProviderState(str, Enum):
    READY = "ready"
    SUCCESS = "success"
    EMPTY = "empty"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class EntityType(str, Enum):
    PERSON = "PERSON"
    ACCOUNT = "ACCOUNT"
    ORGANIZATION = "ORGANIZATION"
    PROJECT = "PROJECT"
    EVENT = "EVENT"
    PUBLICATION = "PUBLICATION"
    ALIAS = "ALIAS"


class EntityRelation(str, Enum):
    HAS_ACCOUNT = "HAS_ACCOUNT"
    ALIAS_OF = "ALIAS_OF"
    AFFILIATED_WITH = "AFFILIATED_WITH"
    CONTRIBUTES_TO = "CONTRIBUTES_TO"
    PARTICIPATED_IN = "PARTICIPATED_IN"
    AUTHORED = "AUTHORED"
    MENTIONS = "MENTIONS"
    LINKS_TO = "LINKS_TO"
    MEMBER_OF = "MEMBER_OF"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"


class Investigation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    subject_label: str = Field(min_length=1, max_length=200)
    context: str | None = Field(default=None, max_length=5000)
    authorized: bool = False
    discovery_mode: str | None = Field(default=None, pattern="^(demo|live|hybrid)$")
    image_sha256: str | None = None
    image_name: str | None = None
    created_at: datetime = Field(default_factory=now_utc)


class ProfileRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
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
    claim: str
    excerpt: str | None = None
    signal_type: str
    weight: float = Field(default=1, ge=0, le=1)
    reliability: float = Field(default=0.5, ge=0, le=1)
    observed_at: datetime = Field(default_factory=now_utc)
    profile_ids: list[UUID] = Field(default_factory=list)
    source_hash: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: EntityType
    label: str = Field(min_length=1, max_length=500)
    canonical_url: HttpUrl | None = None
    aliases: list[str] = Field(default_factory=list)
    source_ids: list[UUID] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    first_seen: datetime = Field(default_factory=now_utc)
    last_seen: datetime = Field(default_factory=now_utc)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityRelationship(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    from_entity_id: UUID
    to_entity_id: UUID
    relation_type: EntityRelation
    evidence_ids: list[UUID] = Field(default_factory=list)
    source_ids: list[UUID] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    observed_at: datetime = Field(default_factory=now_utc)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Candidate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    profiles: list[ProfileRecord] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class ResolutionResult(BaseModel):
    candidate_id: UUID
    score: float = Field(ge=0, le=100)
    status: ResolutionStatus
    signals: dict[str, float]
    supporting_evidence: list[UUID] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)


class Relationship(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_entity: str
    relationship: str
    target_entity: str
    evidence_ids: list[UUID] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
