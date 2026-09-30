from datetime import datetime, timedelta, timezone

import pytest

from app.agents.contracts import (
    GISAgentOutput,
    OceanAgentOutput,
    SafetyAgentInput,
    TideStage,
    WeatherAgentOutput,
)
from app.agents.safety import SafetyAgent
from app.schemas.decision import (
    EvidenceItem,
    Recommendation,
    RiskFactor,
    RiskLevel,
    RouteRecommendation,
    SourceType,
)
from app.schemas.trip import (
    GeoPoint,
    TripAnalysisRequest,
    VesselType,
)


def build_risk_factor(
    code: str,
    score: int,
) -> RiskFactor:
    if score >= 85:
        level = RiskLevel.SEVERE
    elif score >= 60:
        level = RiskLevel.HIGH
    elif score >= 30:
        level = RiskLevel.MODERATE
    else:
        level = RiskLevel.LOW

    return RiskFactor(
        code=code,
        label=code.replace("_", " ").title(),
        level=level,
        score=score,
        explanation=f"Prototype risk score is {score}.",
    )


def build_evidence(
    source_name: str,
    source_type: SourceType,
) -> EvidenceItem:
    now = datetime.now(timezone.utc)

    return EvidenceItem(
        source_name=source_name,
        source_type=source_type,
        summary=f"Prototype evidence from {source_name}.",
        observed_at=now,
        retrieved_at=now,
        freshness_minutes=0,
        confidence=0.90,
    )


def build_safety_input(
    *,
    weather_score: int,
    ocean_score: int,
    gis_score: int,
    wind_speed_kmh: float = 15.0,
    wave_height_m: float = 1.0,
    crosses_restricted_zone: bool = False,
) -> SafetyAgentInput:
    request = TripAnalysisRequest(
        query="Is this fishing trip safe for the crew?",
        origin=GeoPoint(
            latitude=19.8135,
            longitude=85.8312,
        ),
        planned_departure=(
            datetime.now(timezone.utc) + timedelta(hours=3)
        ),
        max_distance_km=50,
        vessel_type=VesselType.SMALL_MOTORIZED,
        crew_count=4,
    )

    weather = WeatherAgentOutput(
        wind_speed_kmh=wind_speed_kmh,
        wind_gust_kmh=wind_speed_kmh + 8,
        precipitation_probability=20,
        visibility_km=12,
        active_alerts=[],
        risk_factor=build_risk_factor(
            code="WEATHER_RISK",
            score=weather_score,
        ),
        evidence=[
            build_evidence(
                source_name="Prototype Weather Source",
                source_type=SourceType.FORECAST,
            )
        ],
    )

    ocean = OceanAgentOutput(
        wave_height_m=wave_height_m,
        swell_height_m=wave_height_m + 0.2,
        current_speed_knots=1.2,
        sea_surface_temperature_c=27,
        tide_stage=TideStage.RISING,
        risk_factor=build_risk_factor(
            code="OCEAN_RISK",
            score=ocean_score,
        ),
        evidence=[
            build_evidence(
                source_name="Prototype Ocean Source",
                source_type=SourceType.OBSERVATION,
            )
        ],
    )

    gis = GISAgentOutput(
        route=RouteRecommendation(
            distance_km=25,
            estimated_duration_minutes=90,
            waypoints=[
                GeoPoint(
                    latitude=19.8135,
                    longitude=85.8312,
                ),
                GeoPoint(
                    latitude=19.9000,
                    longitude=85.9500,
                ),
            ],
            advisory="Follow the recommended prototype route.",
        ),
        crosses_restricted_zone=crosses_restricted_zone,
        geofence_names=(
            ["Prototype Protected Zone"]
            if crosses_restricted_zone
            else []
        ),
        risk_factor=build_risk_factor(
            code="GIS_RISK",
            score=gis_score,
        ),
        evidence=[
            build_evidence(
                source_name="Prototype GIS Source",
                source_type=SourceType.GEOSPATIAL,
            )
        ],
    )

    return SafetyAgentInput(
        request=request,
        weather=weather,
        ocean=ocean,
        gis=gis,
    )


@pytest.mark.asyncio
async def test_safe_conditions_recommend_proceed() -> None:
    safety_agent = SafetyAgent()

    result = await safety_agent.run(
        build_safety_input(
            weather_score=10,
            ocean_score=10,
            gis_score=10,
        )
    )

    assert result.recommendation == Recommendation.PROCEED
    assert result.risk_level == RiskLevel.LOW
    assert result.safety_score == 90
    assert result.confidence > 0
    assert len(result.evidence) >= 4


@pytest.mark.asyncio
async def test_moderate_conditions_recommend_caution() -> None:
    safety_agent = SafetyAgent()

    result = await safety_agent.run(
        build_safety_input(
            weather_score=40,
            ocean_score=50,
            gis_score=30,
        )
    )

    assert (
        result.recommendation
        == Recommendation.PROCEED_WITH_CAUTION
    )
    assert result.risk_level == RiskLevel.MODERATE
    assert 0 < result.safety_score < 70
    assert len(result.safety_instructions) >= 1


@pytest.mark.asyncio
async def test_restricted_zone_recommends_do_not_proceed() -> None:
    safety_agent = SafetyAgent()

    result = await safety_agent.run(
        build_safety_input(
            weather_score=10,
            ocean_score=10,
            gis_score=20,
            crosses_restricted_zone=True,
        )
    )

    assert (
        result.recommendation
        == Recommendation.DO_NOT_PROCEED
    )
    assert result.risk_level == RiskLevel.SEVERE
    assert result.safety_score <= 15
    assert any(
        "restricted" in reason.lower()
        for reason in result.reasons
    )
    assert len(result.alerts) >= 1


@pytest.mark.asyncio
async def test_vessel_limit_violation_blocks_trip() -> None:
    safety_agent = SafetyAgent()

    result = await safety_agent.run(
        build_safety_input(
            weather_score=20,
            ocean_score=20,
            gis_score=10,
            wind_speed_kmh=50,
            wave_height_m=4,
        )
    )

    assert (
        result.recommendation
        == Recommendation.DO_NOT_PROCEED
    )
    assert any(
        risk.code == "VESSEL_CONDITION_MISMATCH"
        for risk in result.risk_factors
    )