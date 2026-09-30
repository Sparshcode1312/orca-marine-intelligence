from datetime import datetime, timedelta, timezone

from app.agents.contracts import WeatherAgentOutput
from app.schemas.decision import (
    AgentName,
    EvidenceItem,
    RiskFactor,
    RiskLevel,
    SourceType,
)
from app.schemas.trip import TripAnalysisRequest


class WeatherAgent:
    """
    Evaluates marine weather conditions.

    This version uses deterministic prototype observations.
    Official IMD data will replace these observations later.
    """

    @property
    def name(self) -> AgentName:
        return AgentName.WEATHER

    @staticmethod
    def calculate_weather_risk_score(
        wind_speed_kmh: float,
        wind_gust_kmh: float,
        precipitation_probability: int,
        visibility_km: float,
    ) -> int:
        wind_risk = min(
            100,
            (wind_speed_kmh / 45) * 100,
        )

        gust_risk = min(
            100,
            (wind_gust_kmh / 60) * 100,
        )

        precipitation_risk = float(
            precipitation_probability
        )

        visibility_risk = max(
            0,
            min(
                100,
                ((10 - visibility_km) / 10) * 100,
            ),
        )

        weighted_score = round(
            wind_risk * 0.35
            + gust_risk * 0.25
            + precipitation_risk * 0.20
            + visibility_risk * 0.20
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

    @staticmethod
    def build_prototype_observation(
        request: TripAnalysisRequest,
    ) -> tuple[float, float, int, float]:
        """
        Produce predictable prototype values based on the
        planned local departure hour.
        """

        departure_hour = request.planned_departure.hour

        if 5 <= departure_hour < 10:
            return (
                16.5,  # Wind speed in km/h
                24.0,  # Wind gust in km/h
                20,    # Rain probability
                9.0,   # Visibility in kilometres
            )

        if 10 <= departure_hour < 15:
            return (
                24.0,
                34.0,
                35,
                7.0,
            )

        if 15 <= departure_hour < 20:
            return (
                31.0,
                44.0,
                58,
                4.5,
            )

        return (
            27.0,
            39.0,
            45,
            5.5,
        )

    async def run(
        self,
        request: TripAnalysisRequest,
    ) -> WeatherAgentOutput:
        (
            wind_speed_kmh,
            wind_gust_kmh,
            precipitation_probability,
            visibility_km,
        ) = self.build_prototype_observation(request)

        risk_score = self.calculate_weather_risk_score(
            wind_speed_kmh=wind_speed_kmh,
            wind_gust_kmh=wind_gust_kmh,
            precipitation_probability=(
                precipitation_probability
            ),
            visibility_km=visibility_km,
        )

        risk_level = self.classify_risk(
            risk_score
        )

        active_alerts: list[str] = []

        if wind_speed_kmh >= 30:
            active_alerts.append(
                "Strong prototype marine winds detected."
            )

        if wind_gust_kmh >= 40:
            active_alerts.append(
                "Prototype wind gusts may affect small vessels."
            )

        if precipitation_probability >= 50:
            active_alerts.append(
                "Elevated prototype rainfall probability."
            )

        if visibility_km < 5:
            active_alerts.append(
                "Reduced prototype visibility may affect navigation."
            )

        generated_at = datetime.now(timezone.utc)

        evidence = EvidenceItem(
            source_name="Prototype IMD-Compatible Weather Feed",
            source_type=SourceType.FORECAST,
            summary=(
                f"Prototype forecast indicates wind at "
                f"{wind_speed_kmh} km/h, gusts at "
                f"{wind_gust_kmh} km/h, rainfall probability "
                f"of {precipitation_probability}% and "
                f"visibility of {visibility_km} km."
            ),
            observed_at=(
                generated_at
                - timedelta(minutes=18)
            ),
            retrieved_at=generated_at,
            freshness_minutes=18,
            confidence=0.88,
        )

        risk_factor = RiskFactor(
            code="WEATHER_RISK",
            label="Marine weather conditions",
            level=risk_level,
            score=risk_score,
            explanation=(
                "The score combines wind speed, gusts, "
                "rainfall probability and visibility using "
                "fixed prototype safety weights."
            ),
        )

        return WeatherAgentOutput(
            wind_speed_kmh=wind_speed_kmh,
            wind_gust_kmh=wind_gust_kmh,
            precipitation_probability=(
                precipitation_probability
            ),
            visibility_km=visibility_km,
            active_alerts=active_alerts,
            risk_factor=risk_factor,
            evidence=[evidence],
        )