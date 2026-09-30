from datetime import datetime, timedelta, timezone

from app.agents.contracts import (
    OceanAgentOutput,
    TideStage,
)
from app.schemas.decision import (
    AgentName,
    EvidenceItem,
    RiskFactor,
    RiskLevel,
    SourceType,
)
from app.schemas.trip import TripAnalysisRequest


class OceanAgent:
    """
    Evaluates ocean and sea-state conditions.

    This implementation uses deterministic prototype data.
    Official INCOIS observations will replace it later.
    """

    TIDE_RISK_SCORES = {
        TideStage.LOW: 15,
        TideStage.RISING: 20,
        TideStage.HIGH: 35,
        TideStage.FALLING: 25,
        TideStage.UNKNOWN: 50,
    }

    @property
    def name(self) -> AgentName:
        return AgentName.OCEAN

    @staticmethod
    def build_prototype_observation(
        request: TripAnalysisRequest,
    ) -> tuple[
        float,
        float,
        float,
        float,
        TideStage,
    ]:
        departure_hour = request.planned_departure.hour

        if 5 <= departure_hour < 10:
            return (
                1.4,                # Wave height in metres
                1.7,                # Swell height in metres
                0.8,                # Current speed in knots
                28.2,               # Sea-surface temperature
                TideStage.RISING,
            )

        if 10 <= departure_hour < 15:
            return (
                1.9,
                2.2,
                1.1,
                28.6,
                TideStage.HIGH,
            )

        if 15 <= departure_hour < 20:
            return (
                2.7,
                3.1,
                1.8,
                29.0,
                TideStage.FALLING,
            )

        return (
            2.1,
            2.5,
            1.4,
            28.7,
            TideStage.LOW,
        )

    @classmethod
    def calculate_ocean_risk_score(
        cls,
        wave_height_m: float,
        swell_height_m: float,
        current_speed_knots: float,
        tide_stage: TideStage,
    ) -> int:
        wave_risk = min(
            100,
            (wave_height_m / 4) * 100,
        )

        swell_risk = min(
            100,
            (swell_height_m / 4) * 100,
        )

        current_risk = min(
            100,
            (current_speed_knots / 3) * 100,
        )

        tide_risk = cls.TIDE_RISK_SCORES[
            tide_stage
        ]

        weighted_score = round(
            wave_risk * 0.45
            + swell_risk * 0.20
            + current_risk * 0.20
            + tide_risk * 0.15
        )

        return max(
            0,
            min(100, weighted_score),
        )

    @staticmethod
    def classify_risk(
        score: int,
    ) -> RiskLevel:
        if score >= 75:
            return RiskLevel.SEVERE

        if score >= 55:
            return RiskLevel.HIGH

        if score >= 30:
            return RiskLevel.MODERATE

        return RiskLevel.LOW

    async def run(
        self,
        request: TripAnalysisRequest,
    ) -> OceanAgentOutput:
        (
            wave_height_m,
            swell_height_m,
            current_speed_knots,
            sea_surface_temperature_c,
            tide_stage,
        ) = self.build_prototype_observation(request)

        risk_score = self.calculate_ocean_risk_score(
            wave_height_m=wave_height_m,
            swell_height_m=swell_height_m,
            current_speed_knots=(
                current_speed_knots
            ),
            tide_stage=tide_stage,
        )

        risk_level = self.classify_risk(
            risk_score
        )

        generated_at = datetime.now(timezone.utc)

        evidence = EvidenceItem(
            source_name="Prototype INCOIS-Compatible Ocean Feed",
            source_type=SourceType.OBSERVATION,
            summary=(
                f"Prototype sea-state observation reports "
                f"{wave_height_m} m waves, "
                f"{swell_height_m} m swell, "
                f"{current_speed_knots} knot current, "
                f"{sea_surface_temperature_c}°C sea-surface "
                f"temperature and {tide_stage.value} tide."
            ),
            observed_at=(
                generated_at
                - timedelta(minutes=12)
            ),
            retrieved_at=generated_at,
            freshness_minutes=12,
            confidence=0.86,
        )

        risk_factor = RiskFactor(
            code="OCEAN_STATE_RISK",
            label="Ocean and sea-state conditions",
            level=risk_level,
            score=risk_score,
            explanation=(
                "The score combines wave height, swell height, "
                "current speed and tide stage using fixed "
                "prototype safety weights."
            ),
        )

        return OceanAgentOutput(
            wave_height_m=wave_height_m,
            swell_height_m=swell_height_m,
            current_speed_knots=(
                current_speed_knots
            ),
            sea_surface_temperature_c=(
                sea_surface_temperature_c
            ),
            tide_stage=tide_stage,
            risk_factor=risk_factor,
            evidence=[evidence],
        )