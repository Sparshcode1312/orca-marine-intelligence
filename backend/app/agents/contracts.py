from enum import Enum
from typing import Generic, Literal, Protocol, TypeAlias, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.decision import (
    AgentName,
    EvidenceItem,
    FishingZoneRecommendation,
    Recommendation,
    RiskFactor,
    RiskLevel,
    RouteRecommendation,
)
from app.schemas.trip import TripAnalysisRequest


class TideStage(str, Enum):
    LOW = "low"
    RISING = "rising"
    HIGH = "high"
    FALLING = "falling"
    UNKNOWN = "unknown"


class PlannerOutput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    agent: Literal[AgentName.PLANNER] = AgentName.PLANNER

    selected_agents: list[AgentName] = Field(
        min_length=1,
        max_length=6,
    )

    reasoning: str = Field(
        min_length=5,
        max_length=500,
    )


class WeatherAgentOutput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    agent: Literal[AgentName.WEATHER] = AgentName.WEATHER

    wind_speed_kmh: float = Field(
        ge=0,
        le=300,
    )

    wind_gust_kmh: float = Field(
        ge=0,
        le=400,
    )

    precipitation_probability: int = Field(
        ge=0,
        le=100,
    )

    visibility_km: float = Field(
        ge=0,
        le=100,
    )

    active_alerts: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    risk_factor: RiskFactor

    evidence: list[EvidenceItem] = Field(
        min_length=1,
        max_length=10,
    )


class OceanAgentOutput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    agent: Literal[AgentName.OCEAN] = AgentName.OCEAN

    wave_height_m: float = Field(
        ge=0,
        le=30,
    )

    swell_height_m: float = Field(
        ge=0,
        le=30,
    )

    current_speed_knots: float = Field(
        ge=0,
        le=20,
    )

    sea_surface_temperature_c: float = Field(
        ge=-5,
        le=50,
    )

    tide_stage: TideStage

    risk_factor: RiskFactor

    evidence: list[EvidenceItem] = Field(
        min_length=1,
        max_length=10,
    )


class PFZAgentOutput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    agent: Literal[AgentName.PFZ] = AgentName.PFZ

    candidate_zones: list[FishingZoneRecommendation] = Field(
        min_length=1,
        max_length=10,
    )

    selected_zone_id: str = Field(
        min_length=2,
        max_length=50,
    )

    selection_reason: str = Field(
        min_length=5,
        max_length=500,
    )

    evidence: list[EvidenceItem] = Field(
        min_length=1,
        max_length=10,
    )


class GISAgentInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    request: TripAnalysisRequest
    selected_zone: FishingZoneRecommendation


class GISAgentOutput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    agent: Literal[AgentName.GIS] = AgentName.GIS

    route: RouteRecommendation

    crosses_restricted_zone: bool

    geofence_names: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    risk_factor: RiskFactor

    evidence: list[EvidenceItem] = Field(
        min_length=1,
        max_length=10,
    )


class SafetyAgentInput(BaseModel):
    """
    Validated specialist outputs required by the Safety Agent.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    request: TripAnalysisRequest
    weather: WeatherAgentOutput
    ocean: OceanAgentOutput
    gis: GISAgentOutput


class SafetyAgentOutput(BaseModel):
    """
    Consolidated safety assessment produced from weather,
    ocean and geospatial intelligence.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    agent: Literal[AgentName.SAFETY] = AgentName.SAFETY

    recommendation: Recommendation
    risk_level: RiskLevel

    safety_score: int = Field(
        ge=0,
        le=100,
        description="Higher values represent safer trip conditions.",
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

    safety_instructions: list[str] = Field(
        min_length=1,
        max_length=10,
    )

    risk_factors: list[RiskFactor] = Field(
        min_length=1,
        max_length=20,
    )

    evidence: list[EvidenceItem] = Field(
        min_length=1,
        max_length=30,
    )


class AgentError(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    agent: AgentName

    code: str = Field(
        pattern=r"^[A-Z][A-Z0-9_]{1,49}$",
    )

    message: str = Field(
        min_length=5,
        max_length=500,
    )

    retryable: bool = False


AgentOutput: TypeAlias = (
    PlannerOutput
    | WeatherAgentOutput
    | OceanAgentOutput
    | PFZAgentOutput
    | GISAgentOutput
    | SafetyAgentOutput
)


InputType = TypeVar(
    "InputType",
    bound=BaseModel,
    contravariant=True,
)

OutputType = TypeVar(
    "OutputType",
    bound=AgentOutput,
    covariant=True,
)


class SpecialistAgent(
    Protocol,
    Generic[InputType, OutputType],
):
    """
    Common interface implemented by every ORCA specialist agent.
    """

    @property
    def name(self) -> AgentName:
        ...

    async def run(
        self,
        input_data: InputType,
    ) -> OutputType:
        ...