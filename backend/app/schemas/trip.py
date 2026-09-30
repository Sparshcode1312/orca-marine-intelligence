from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LanguageCode(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    ODIA = "or"


class VesselType(str, Enum):
    TRADITIONAL = "traditional"
    SMALL_MOTORIZED = "small_motorized"
    TRAWLER = "trawler"


class GeoPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(
        ge=-90,
        le=90,
        description="Latitude in decimal degrees.",
    )

    longitude: float = Field(
        ge=-180,
        le=180,
        description="Longitude in decimal degrees.",
    )


class TripAnalysisRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    request_id: UUID = Field(default_factory=uuid4)

    query: str = Field(
        min_length=5,
        max_length=500,
        description="User's marine or fishing-related question.",
    )

    language: LanguageCode = LanguageCode.ENGLISH

    origin: GeoPoint

    planned_departure: datetime = Field(
        description="Timezone-aware planned departure time."
    )

    max_distance_km: float = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum distance the user plans to travel.",
    )

    vessel_type: VesselType = VesselType.SMALL_MOTORIZED

    crew_count: int = Field(
        default=1,
        ge=1,
        le=50,
    )

    include_explanation: bool = True

    @field_validator("planned_departure")
    @classmethod
    def validate_planned_departure(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "planned_departure must include timezone information"
            )

        departure_utc = value.astimezone(timezone.utc)
        current_time = datetime.now(timezone.utc)

        if departure_utc < current_time - timedelta(minutes=15):
            raise ValueError(
                "planned_departure cannot be in the past"
            )

        if departure_utc > current_time + timedelta(days=7):
            raise ValueError(
                "planned_departure cannot be more than 7 days ahead"
            )

        return value


class TripValidationResponse(BaseModel):
    accepted: bool
    message: str
    request: TripAnalysisRequest