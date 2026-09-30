from datetime import datetime, timezone

from app.agents.contracts import (
    SafetyAgentInput,
    SafetyAgentOutput,
)
from app.schemas.decision import (
    AgentName,
    EvidenceItem,
    Recommendation,
    RiskFactor,
    RiskLevel,
    SourceType,
)
from app.schemas.trip import VesselType


class SafetyAgent:
    """
    Combines weather, ocean and GIS intelligence into one
    deterministic and explainable marine-safety decision.

    This prototype uses transparent safety rules. It must not be
    treated as an official maritime advisory.
    """

    @property
    def name(self) -> AgentName:
        return AgentName.SAFETY

    async def run(
        self,
        input_data: SafetyAgentInput,
    ) -> SafetyAgentOutput:
        weather = input_data.weather
        ocean = input_data.ocean
        gis = input_data.gis
        request = input_data.request

        risk_factors = [
            weather.risk_factor,
            ocean.risk_factor,
            gis.risk_factor,
        ]

        vessel_risk = self._evaluate_vessel_compatibility(
            vessel_type=request.vessel_type,
            wind_speed_kmh=weather.wind_speed_kmh,
            wave_height_m=ocean.wave_height_m,
        )

        if vessel_risk is not None:
            risk_factors.append(vessel_risk)

        weighted_risk_score = self._calculate_weighted_risk(
            weather_score=weather.risk_factor.score,
            ocean_score=ocean.risk_factor.score,
            gis_score=gis.risk_factor.score,
        )

        hard_stop_reasons = self._find_hard_stop_reasons(
            input_data=input_data,
            vessel_risk=vessel_risk,
        )

        if hard_stop_reasons:
            overall_risk_score = max(weighted_risk_score, 85)
        else:
            overall_risk_score = weighted_risk_score

        overall_risk_score = min(max(overall_risk_score, 0), 100)

        risk_level = self._risk_level_from_score(overall_risk_score)

        recommendation = self._recommendation_from_risk(
            risk_score=overall_risk_score,
            hard_stop=bool(hard_stop_reasons),
        )

        safety_score = 100 - overall_risk_score

        evidence = self._combine_evidence(input_data)
        confidence = self._calculate_confidence(evidence)

        reasons = self._build_reasons(
            risk_factors=risk_factors,
            hard_stop_reasons=hard_stop_reasons,
        )

        alerts = self._build_alerts(input_data)
        safety_instructions = self._build_safety_instructions(
            recommendation=recommendation,
            vessel_type=request.vessel_type,
        )

        summary = self._build_summary(
            recommendation=recommendation,
            risk_level=risk_level,
            safety_score=safety_score,
        )

        return SafetyAgentOutput(
            recommendation=recommendation,
            risk_level=risk_level,
            safety_score=safety_score,
            confidence=confidence,
            summary=summary,
            reasons=reasons,
            alerts=alerts,
            safety_instructions=safety_instructions,
            risk_factors=risk_factors,
            evidence=evidence,
        )

    @staticmethod
    def _calculate_weighted_risk(
        weather_score: int,
        ocean_score: int,
        gis_score: int,
    ) -> int:
        """
        Ocean conditions receive the highest weight because waves,
        swell and currents directly affect small-vessel stability.
        """

        weighted_score = (
            weather_score * 0.35
            + ocean_score * 0.40
            + gis_score * 0.25
        )

        return round(weighted_score)

    @staticmethod
    def _evaluate_vessel_compatibility(
        vessel_type: VesselType,
        wind_speed_kmh: float,
        wave_height_m: float,
    ) -> RiskFactor | None:
        limits = {
            VesselType.TRADITIONAL: {
                "wind": 25.0,
                "wave": 1.5,
            },
            VesselType.SMALL_MOTORIZED: {
                "wind": 35.0,
                "wave": 2.5,
            },
            VesselType.TRAWLER: {
                "wind": 45.0,
                "wave": 3.5,
            },
        }

        vessel_limits = limits[vessel_type]

        wind_exceeded = wind_speed_kmh > vessel_limits["wind"]
        wave_exceeded = wave_height_m > vessel_limits["wave"]

        if not wind_exceeded and not wave_exceeded:
            return None

        if wind_exceeded and wave_exceeded:
            score = 90
            level = RiskLevel.SEVERE
            explanation = (
                f"Wind speed of {wind_speed_kmh:.1f} km/h and wave height "
                f"of {wave_height_m:.1f} m exceed the prototype safety "
                f"limits for a {vessel_type.value} vessel."
            )
        else:
            score = 70
            level = RiskLevel.HIGH

            exceeded_condition = (
                f"wind speed of {wind_speed_kmh:.1f} km/h"
                if wind_exceeded
                else f"wave height of {wave_height_m:.1f} m"
            )

            explanation = (
                f"The {exceeded_condition} exceeds the prototype safety "
                f"limit for a {vessel_type.value} vessel."
            )

        return RiskFactor(
            code="VESSEL_CONDITION_MISMATCH",
            label="Vessel and sea-condition mismatch",
            level=level,
            score=score,
            explanation=explanation,
        )

    @staticmethod
    def _find_hard_stop_reasons(
        input_data: SafetyAgentInput,
        vessel_risk: RiskFactor | None,
    ) -> list[str]:
        reasons: list[str] = []

        if input_data.gis.crosses_restricted_zone:
            reasons.append(
                "The planned route intersects a restricted or protected zone."
            )

        if input_data.weather.risk_factor.level == RiskLevel.SEVERE:
            reasons.append(
                "Severe weather risk was detected for the planned trip."
            )

        if input_data.ocean.risk_factor.level == RiskLevel.SEVERE:
            reasons.append(
                "Severe ocean-condition risk was detected."
            )

        if (
            vessel_risk is not None
            and vessel_risk.level == RiskLevel.SEVERE
        ):
            reasons.append(
                "The forecast conditions exceed the vessel's safe "
                "prototype operating limits."
            )

        return reasons

    @staticmethod
    def _risk_level_from_score(score: int) -> RiskLevel:
        if score >= 85:
            return RiskLevel.SEVERE

        if score >= 60:
            return RiskLevel.HIGH

        if score >= 30:
            return RiskLevel.MODERATE

        return RiskLevel.LOW

    @staticmethod
    def _recommendation_from_risk(
        risk_score: int,
        hard_stop: bool,
    ) -> Recommendation:
        if hard_stop or risk_score >= 75:
            return Recommendation.DO_NOT_PROCEED

        if risk_score >= 30:
            return Recommendation.PROCEED_WITH_CAUTION

        return Recommendation.PROCEED

    @staticmethod
    def _combine_evidence(
        input_data: SafetyAgentInput,
    ) -> list[EvidenceItem]:
        specialist_evidence = [
            *input_data.weather.evidence,
            *input_data.ocean.evidence,
            *input_data.gis.evidence,
        ]

        now = datetime.now(timezone.utc)

        safety_rule_evidence = EvidenceItem(
            source_name="ORCA Prototype Safety Rules",
            source_type=SourceType.SAFETY_RULE,
            summary=(
                "Deterministic safety rules evaluated weather, ocean, "
                "route and vessel-operating conditions."
            ),
            observed_at=now,
            retrieved_at=now,
            freshness_minutes=0,
            confidence=0.95,
        )

        # Reserve one position for the Safety Agent's own evidence.
        return [
            *specialist_evidence[:29],
            safety_rule_evidence,
        ]

    @staticmethod
    def _calculate_confidence(
        evidence: list[EvidenceItem],
    ) -> float:
        if not evidence:
            return 0.0

        average_confidence = sum(
            item.confidence for item in evidence
        ) / len(evidence)

        return round(average_confidence, 2)

    @staticmethod
    def _build_reasons(
        risk_factors: list[RiskFactor],
        hard_stop_reasons: list[str],
    ) -> list[str]:
        if hard_stop_reasons:
            reasons = hard_stop_reasons.copy()
        else:
            ordered_risks = sorted(
                risk_factors,
                key=lambda risk: risk.score,
                reverse=True,
            )

            reasons = [
                risk.explanation
                for risk in ordered_risks[:3]
            ]

        return reasons[:10]

    @staticmethod
    def _build_alerts(
        input_data: SafetyAgentInput,
    ) -> list[str]:
        alerts = list(input_data.weather.active_alerts)

        if input_data.gis.crosses_restricted_zone:
            geofences = ", ".join(input_data.gis.geofence_names)

            if geofences:
                alerts.append(
                    f"Restricted-route warning: {geofences}."
                )
            else:
                alerts.append(
                    "The route intersects a restricted marine zone."
                )

        # Remove duplicate alerts while preserving their order.
        return list(dict.fromkeys(alerts))[:10]

    @staticmethod
    def _build_safety_instructions(
        recommendation: Recommendation,
        vessel_type: VesselType,
    ) -> list[str]:
        common_instructions = [
            "Carry functional life jackets for every crew member.",
            "Verify fuel, engine, navigation lights and communication equipment.",
            "Share the planned route and expected return time with a shore contact.",
            "Check official local weather and maritime advisories before departure.",
        ]

        if recommendation == Recommendation.DO_NOT_PROCEED:
            return [
                "Do not begin the trip under the assessed conditions.",
                "Wait for safer weather, ocean and route conditions.",
                "Consult the relevant local maritime authority before departure.",
                *common_instructions,
            ][:10]

        if recommendation == Recommendation.PROCEED_WITH_CAUTION:
            return [
                f"Operate the {vessel_type.value} vessel conservatively.",
                "Avoid extending the trip beyond the recommended route.",
                "Monitor weather and sea conditions throughout the trip.",
                "Return immediately if visibility or vessel stability worsens.",
                *common_instructions,
            ][:10]

        return [
            "Continue monitoring weather and ocean conditions.",
            "Remain within the planned route and operating distance.",
            *common_instructions,
        ][:10]

    @staticmethod
    def _build_summary(
        recommendation: Recommendation,
        risk_level: RiskLevel,
        safety_score: int,
    ) -> str:
        summaries = {
            Recommendation.PROCEED: (
                "Conditions are currently within the prototype safety "
                "limits for the planned trip."
            ),
            Recommendation.PROCEED_WITH_CAUTION: (
                "The trip may proceed only with caution because one or "
                "more conditions require increased attention."
            ),
            Recommendation.DO_NOT_PROCEED: (
                "The trip should not proceed because unsafe conditions "
                "or a mandatory safety restriction was detected."
            ),
            Recommendation.INSUFFICIENT_DATA: (
                "The system does not have enough reliable information "
                "to provide a safe trip recommendation."
            ),
        }

        return (
            f"{summaries[recommendation]} "
            f"Overall risk is {risk_level.value}, with a safety score "
            f"of {safety_score} out of 100."
        )