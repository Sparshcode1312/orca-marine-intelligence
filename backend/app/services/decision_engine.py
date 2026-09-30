from datetime import datetime, timedelta, timezone
from app.utils.geo import calculate_distance_km

from app.schemas.decision import (
    AgentExecution,
    AgentName,
    AgentStatus,
    EvidenceItem,
    FishingZoneRecommendation,
    IntelligenceDecision,
    Recommendation,
    RiskFactor,
    RiskLevel,
    RouteRecommendation,
    SourceType,
)
from app.schemas.trip import GeoPoint, TripAnalysisRequest


def create_agent_execution(
    agent: AgentName,
    start_time: datetime,
    duration_ms: int,
    evidence_count: int,
) -> AgentExecution:
    return AgentExecution(
        agent=agent,
        status=AgentStatus.SUCCEEDED,
        started_at=start_time,
        completed_at=start_time
        + timedelta(milliseconds=duration_ms),
        evidence_count=evidence_count,
    )


def calculate_risk_level(
    safety_score: int,
) -> RiskLevel:
    if safety_score >= 80:
        return RiskLevel.LOW

    if safety_score >= 55:
        return RiskLevel.MODERATE

    if safety_score >= 30:
        return RiskLevel.HIGH

    return RiskLevel.SEVERE


def calculate_recommendation(
    safety_score: int,
    zone_within_range: bool,
) -> Recommendation:
    if not zone_within_range:
        return Recommendation.DO_NOT_PROCEED

    if safety_score >= 80:
        return Recommendation.PROCEED

    if safety_score >= 55:
        return Recommendation.PROCEED_WITH_CAUTION

    return Recommendation.DO_NOT_PROCEED


def build_prototype_decision(
    request: TripAnalysisRequest,
) -> IntelligenceDecision:
    """
    Build an evidence-grounded prototype decision.

    All observations in this function are representative mock data.
    They will be replaced by official data adapters later.
    """

    generated_at = datetime.now(timezone.utc)

    # The temporary zone remains close to the user's origin.
    # Later, this will come from INCOIS PFZ data.
    zone_center = GeoPoint(
        latitude=max(
            -89.5,
            min(
                89.5,
                request.origin.latitude - 0.12,
            ),
        ),
        longitude=max(
            -179.5,
            min(
                179.5,
                request.origin.longitude + 0.16,
            ),
        ),
    )

    zone_distance_km = calculate_distance_km(
        request.origin,
        zone_center,
    )

    zone_within_range = (
        zone_distance_km
        <= request.max_distance_km
    )

    midpoint = GeoPoint(
        latitude=round(
            (
                request.origin.latitude
                + zone_center.latitude
            )
            / 2,
            6,
        ),
        longitude=round(
            (
                request.origin.longitude
                + zone_center.longitude
            )
            / 2,
            6,
        ),
    )

    # Prototype risk values.
    weather_risk_score = 18
    wave_risk_score = 44
    geofence_risk_score = 5

    weighted_risk_score = round(
        weather_risk_score * 0.35
        + wave_risk_score * 0.45
        + geofence_risk_score * 0.20
    )

    safety_score = max(
        0,
        min(
            100,
            100 - weighted_risk_score,
        ),
    )

    risk_level = calculate_risk_level(
        safety_score
    )

    recommendation = calculate_recommendation(
        safety_score=safety_score,
        zone_within_range=zone_within_range,
    )

    alerts: list[str] = [
        (
            "Wave height may increase after 12:30. "
            "Return before the recommended window closes."
        )
    ]

    if not zone_within_range:
        alerts.append(
            "The prototype fishing zone exceeds the "
            "selected maximum travel distance."
        )

    risk_factors = [
        RiskFactor(
            code="WEATHER_RISK",
            label="Weather conditions",
            level=RiskLevel.LOW,
            score=weather_risk_score,
            explanation=(
                "Prototype forecast indicates stable "
                "weather during the early morning."
            ),
        ),
        RiskFactor(
            code="WAVE_RISK",
            label="Wave conditions",
            level=RiskLevel.MODERATE,
            score=wave_risk_score,
            explanation=(
                "Prototype wave conditions remain manageable "
                "early but may increase after midday."
            ),
        ),
        RiskFactor(
            code="GEOFENCE_RISK",
            label="Restricted-zone exposure",
            level=RiskLevel.LOW,
            score=geofence_risk_score,
            explanation=(
                "The prototype route does not intersect "
                "a known restricted-zone boundary."
            ),
        ),
    ]

    evidence = [
        EvidenceItem(
            source_name="Prototype IMD Marine Forecast",
            source_type=SourceType.FORECAST,
            summary=(
                "Early-morning weather remains stable, "
                "with increasing marine risk later in the day."
            ),
            observed_at=generated_at
            - timedelta(minutes=18),
            retrieved_at=generated_at,
            freshness_minutes=18,
            confidence=0.88,
        ),
        EvidenceItem(
            source_name="Prototype INCOIS PFZ Advisory",
            source_type=SourceType.ADVISORY,
            summary=(
                "Ocean conditions indicate a potentially "
                "suitable fishing zone near the selected origin."
            ),
            observed_at=generated_at
            - timedelta(minutes=42),
            retrieved_at=generated_at,
            freshness_minutes=42,
            confidence=0.84,
        ),
        EvidenceItem(
            source_name="Prototype GIS Route Check",
            source_type=SourceType.GEOSPATIAL,
            summary=(
                "The generated route avoids the prototype "
                "restricted and high-risk areas."
            ),
            observed_at=generated_at
            - timedelta(minutes=5),
            retrieved_at=generated_at,
            freshness_minutes=5,
            confidence=0.91,
        ),
        EvidenceItem(
            source_name="ORCA Deterministic Safety Rules",
            source_type=SourceType.SAFETY_RULE,
            summary=(
                "Weather, wave and geofence scores were "
                "combined using fixed safety weights."
            ),
            observed_at=generated_at,
            retrieved_at=generated_at,
            freshness_minutes=0,
            confidence=1.0,
        ),
    ]

    average_confidence = round(
        sum(item.confidence for item in evidence)
        / len(evidence),
        2,
    )

    recommended_zone = FishingZoneRecommendation(
        zone_id="PFZ-PROTOTYPE-17",
        name="Prototype Coastal Fishing Zone 17",
        center=zone_center,
        suitability_score=84,
        distance_km=zone_distance_km,
        recommended_from=request.planned_departure,
        recommended_until=(
            request.planned_departure
            + timedelta(hours=6)
        ),
    )

    recommended_route = RouteRecommendation(
        distance_km=zone_distance_km,
        estimated_duration_minutes=max(
            15,
            round(zone_distance_km * 3),
        ),
        waypoints=[
            request.origin,
            midpoint,
            zone_center,
        ],
        advisory=(
            "Follow the suggested route and return before "
            "12:30 if wave conditions begin to increase."
        ),
    )

    agent_executions = [
        create_agent_execution(
            AgentName.PLANNER,
            generated_at,
            duration_ms=40,
            evidence_count=0,
        ),
        create_agent_execution(
            AgentName.WEATHER,
            generated_at + timedelta(milliseconds=45),
            duration_ms=90,
            evidence_count=1,
        ),
        create_agent_execution(
            AgentName.OCEAN,
            generated_at + timedelta(milliseconds=50),
            duration_ms=110,
            evidence_count=1,
        ),
        create_agent_execution(
            AgentName.PFZ,
            generated_at + timedelta(milliseconds=55),
            duration_ms=125,
            evidence_count=1,
        ),
        create_agent_execution(
            AgentName.GIS,
            generated_at + timedelta(milliseconds=60),
            duration_ms=100,
            evidence_count=1,
        ),
        create_agent_execution(
            AgentName.SAFETY,
            generated_at + timedelta(milliseconds=190),
            duration_ms=55,
            evidence_count=4,
        ),
    ]

    summary = (
        "The prototype fishing zone is suitable during the "
        "early-morning window, but the trip requires caution "
        "because wave conditions may increase later."
    )

    if not zone_within_range:
        summary = (
            "The identified prototype fishing zone exceeds "
            "the maximum distance selected for this trip."
        )

    return IntelligenceDecision(
        request_id=request.request_id,
        recommendation=recommendation,
        risk_level=risk_level,
        safety_score=safety_score,
        confidence=average_confidence,
        summary=summary,
        reasons=[
            (
                "Prototype PFZ conditions indicate "
                "favourable fishing potential."
            ),
            (
                "Early-morning weather risk is currently low."
            ),
            (
                "Wave conditions require the vessel "
                "to return before the risk increases."
            ),
        ],
        alerts=alerts,
        risk_factors=risk_factors,
        evidence=evidence,
        agent_executions=agent_executions,
        recommended_zone=recommended_zone,
        recommended_route=recommended_route,
        prototype_data=True,
        human_verification_required=True,
    )