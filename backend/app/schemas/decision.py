from datetime import datetime, timezone
from enum import Enum
from typing import Self
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from app.schemas.trip import GeoPoint


class Recommendation(str, Enum):
    PROCEED = "proceed"
    PROCEED_WITH_CAUTION = "proceed_with_caution"
    DO_NOT_PROCEED = "do_not_proceed"
    INSUFFICIENT_DATA = "insufficient_data"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    ADVISORY = "advisory"
    FORECAST = "forecast"
    OBSERVATION = "observation"
    SATELLITE = "satellite"
    GEOSPATIAL = "geospatial"
    SAFETY_RULE = "safety_rule"


class AgentName(str, Enum):
    PLANNER = "planner"
    WEATHER = "weather"
    OCEAN = "ocean"
    PFZ = "pfz"
    GIS = "gis"
    SAFETY = "safety"


class AgentStatus(str, Enum):
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    source_name: str = Field(
        min_length=2,
        max_length=100,
    )

    source_type: SourceType

    summary: str = Field(
        min_length=5,
        max_length=500,
    )

    observed_at: datetime

    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    freshness_minutes: int = Field(
        ge=0,
        le=10080,
        description="Age of the source data in minutes.",
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    reference_url: HttpUrl | None = None

    @field_validator("observed_at", "retrieved_at")
    @classmethod
    def timestamps_must_have_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Evidence timestamps must include timezone information"
            )

        return value


class RiskFactor(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    code: str = Field(
        pattern=r"^[A-Z][A-Z0-9_]{1,39}$",
        examples=["HIGH_WAVE_RISK"],
    )

    label: str = Field(
        min_length=2,
        max_length=100,
    )

    level: RiskLevel

    score: int = Field(
        ge=0,
        le=100,
        description="Higher values represent greater risk.",
    )

    explanation: str = Field(
        min_length=5,
        max_length=500,
    )


class AgentExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: AgentName
    status: AgentStatus

    started_at: datetime
    completed_at: datetime

    evidence_count: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    error_code: str | None = Field(
        default=None,
        pattern=r"^[A-Z][A-Z0-9_]{1,49}$",
    )

    @model_validator(mode="after")
    def validate_execution(self) -> Self:
        if self.started_at.tzinfo is None:
            raise ValueError(
                "started_at must include timezone information"
            )

        if self.completed_at.tzinfo is None:
            raise ValueError(
                "completed_at must include timezone information"
            )

        if self.completed_at < self.started_at:
            raise ValueError(
                "completed_at cannot be earlier than started_at"
            )

        if self.status == AgentStatus.FAILED and not self.error_code:
            raise ValueError(
                "A failed agent execution must include error_code"
            )

        if self.status != AgentStatus.FAILED and self.error_code:
            raise ValueError(
                "error_code is only allowed for failed executions"
            )

        return self


class FishingZoneRecommendation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    zone_id: str = Field(
        min_length=2,
        max_length=50,
    )

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    center: GeoPoint

    suitability_score: int = Field(
        ge=0,
        le=100,
        description="Higher values indicate better fishing suitability.",
    )

    distance_km: float = Field(
        ge=0,
        le=500,
    )

    recommended_from: datetime
    recommended_until: datetime

    @model_validator(mode="after")
    def validate_time_window(self) -> Self:
        if self.recommended_from.tzinfo is None:
            raise ValueError(
                "recommended_from must include timezone information"
            )

        if self.recommended_until.tzinfo is None:
            raise ValueError(
                "recommended_until must include timezone information"
            )

        if self.recommended_until <= self.recommended_from:
            raise ValueError(
                "recommended_until must be later than recommended_from"
            )

        return self


class RouteRecommendation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    distance_km: float = Field(
        ge=0,
        le=500,
    )

    estimated_duration_minutes: int = Field(
        ge=1,
        le=1440,
    )

    waypoints: list[GeoPoint] = Field(
        min_length=2,
        max_length=50,
    )

    advisory: str = Field(
        min_length=5,
        max_length=500,
    )


class IntelligenceDecision(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    decision_id: UUID = Field(default_factory=uuid4)
    request_id: UUID

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    recommendation: Recommendation
    risk_level: RiskLevel

    safety_score: int = Field(
        ge=0,
        le=100,
        description="Higher values represent safer conditions.",
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    summary: str = Field(
        min_length=10,
        max_length=1000,
    )

    reasons: list[str] = Field(
        min_length=1,
        max_length=10,
    )

    alerts: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    risk_factors: list[RiskFactor] = Field(
        min_length=1,
        max_length=20,
    )

    evidence: list[EvidenceItem] = Field(
        min_length=1,
        max_length=50,
    )

    agent_executions: list[AgentExecution] = Field(
        min_length=1,
        max_length=20,
    )

    recommended_zone: FishingZoneRecommendation | None = None
    recommended_route: RouteRecommendation | None = None

    prototype_data: bool = True
    human_verification_required: bool = True

    @model_validator(mode="after")
    def validate_decision_consistency(self) -> Self:
        unsafe_levels = {
            RiskLevel.HIGH,
            RiskLevel.SEVERE,
        }

        if (
            self.risk_level in unsafe_levels
            and self.recommendation == Recommendation.PROCEED
        ):
            raise ValueError(
                "A high or severe risk decision cannot recommend proceed"
            )

        if (
            self.recommendation == Recommendation.INSUFFICIENT_DATA
            and self.confidence > 0.5
        ):
            raise ValueError(
                "Insufficient-data decisions cannot have confidence above 0.5"
            )

        if (
            self.prototype_data
            and not self.human_verification_required
        ):
            raise ValueError(
                "Prototype decisions must require human verification"
            )

        return self