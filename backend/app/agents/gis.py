from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.agents.contracts import (
    GISAgentInput,
    GISAgentOutput,
)
from app.schemas.decision import (
    AgentName,
    EvidenceItem,
    RiskFactor,
    RiskLevel,
    RouteRecommendation,
    SourceType,
)
from app.schemas.trip import GeoPoint, VesselType
from app.utils.geo import calculate_distance_km


@dataclass(frozen=True)
class PrototypeRestrictedZone:
    name: str
    center: GeoPoint
    radius_km: float


class GISAgent:
    """
    Creates a route and evaluates prototype geofences.

    Real PostGIS geometry and official restricted-zone layers
    will replace this simplified implementation later.
    """

    VESSEL_SPEEDS_KMH = {
        VesselType.TRADITIONAL: 8.0,
        VesselType.SMALL_MOTORIZED: 18.0,
        VesselType.TRAWLER: 22.0,
    }

    @property
    def name(self) -> AgentName:
        return AgentName.GIS

    @staticmethod
    def create_midpoint(
        start: GeoPoint,
        end: GeoPoint,
    ) -> GeoPoint:
        return GeoPoint(
            latitude=round(
                (start.latitude + end.latitude) / 2,
                6,
            ),
            longitude=round(
                (start.longitude + end.longitude) / 2,
                6,
            ),
        )

    @staticmethod
    def create_restricted_zone(
        origin: GeoPoint,
    ) -> PrototypeRestrictedZone:
        return PrototypeRestrictedZone(
            name="Prototype Marine Conservation Boundary",
            center=GeoPoint(
                latitude=max(
                    -89.5,
                    min(
                        89.5,
                        origin.latitude - 0.065,
                    ),
                ),
                longitude=max(
                    -179.5,
                    min(
                        179.5,
                        origin.longitude + 0.08,
                    ),
                ),
            ),
            radius_km=4.0,
        )

    @staticmethod
    def point_inside_restricted_zone(
        point: GeoPoint,
        restricted_zone: PrototypeRestrictedZone,
    ) -> bool:
        distance_to_center = calculate_distance_km(
            point,
            restricted_zone.center,
        )

        return (
            distance_to_center
            <= restricted_zone.radius_km
        )

    @staticmethod
    def create_detour_point(
        direct_midpoint: GeoPoint,
    ) -> GeoPoint:
        return GeoPoint(
            latitude=max(
                -89.5,
                min(
                    89.5,
                    direct_midpoint.latitude + 0.06,
                ),
            ),
            longitude=direct_midpoint.longitude,
        )

    @staticmethod
    def calculate_route_distance(
        waypoints: list[GeoPoint],
    ) -> float:
        total_distance = 0.0

        for index in range(
            len(waypoints) - 1
        ):
            total_distance += calculate_distance_km(
                waypoints[index],
                waypoints[index + 1],
            )

        return round(total_distance, 2)

    @staticmethod
    def classify_risk(
        risk_score: int,
    ) -> RiskLevel:
        if risk_score >= 75:
            return RiskLevel.SEVERE

        if risk_score >= 55:
            return RiskLevel.HIGH

        if risk_score >= 30:
            return RiskLevel.MODERATE

        return RiskLevel.LOW

    async def run(
        self,
        input_data: GISAgentInput,
    ) -> GISAgentOutput:
        request = input_data.request
        selected_zone = input_data.selected_zone

        direct_midpoint = self.create_midpoint(
            request.origin,
            selected_zone.center,
        )

        restricted_zone = (
            self.create_restricted_zone(
                request.origin
            )
        )

        direct_route_intersects = (
            self.point_inside_restricted_zone(
                direct_midpoint,
                restricted_zone,
            )
        )

        if direct_route_intersects:
            route_midpoint = (
                self.create_detour_point(
                    direct_midpoint
                )
            )
        else:
            route_midpoint = direct_midpoint

        waypoints = [
            request.origin,
            route_midpoint,
            selected_zone.center,
        ]

        route_distance_km = (
            self.calculate_route_distance(
                waypoints
            )
        )

        final_route_intersects = (
            self.point_inside_restricted_zone(
                route_midpoint,
                restricted_zone,
            )
        )

        exceeds_maximum_distance = (
            route_distance_km
            > request.max_distance_km
        )

        if final_route_intersects:
            risk_score = 95
            explanation = (
                "The generated route intersects a prototype "
                "restricted marine boundary."
            )
        elif exceeds_maximum_distance:
            risk_score = 70
            explanation = (
                "The generated route exceeds the maximum "
                "travel distance selected by the user."
            )
        elif direct_route_intersects:
            risk_score = 25
            explanation = (
                "The direct route intersected a prototype "
                "restricted boundary, so a safer detour "
                "was generated."
            )
        else:
            risk_score = 10
            explanation = (
                "The generated route remains clear of the "
                "prototype restricted boundary."
            )

        risk_level = self.classify_risk(
            risk_score
        )

        vessel_speed_kmh = self.VESSEL_SPEEDS_KMH[
            request.vessel_type
        ]

        duration_minutes = max(
            1,
            round(
                (
                    route_distance_km
                    / vessel_speed_kmh
                )
                * 60
            ),
        )

        if direct_route_intersects:
            advisory = (
                "Follow the generated detour and do not "
                "enter the prototype conservation boundary."
            )
        else:
            advisory = (
                "Follow the generated route and continue "
                "monitoring marine alerts."
            )

        route = RouteRecommendation(
            distance_km=route_distance_km,
            estimated_duration_minutes=(
                duration_minutes
            ),
            waypoints=waypoints,
            advisory=advisory,
        )

        generated_at = datetime.now(timezone.utc)

        evidence = EvidenceItem(
            source_name="Prototype GEBCO and OSM Route Layer",
            source_type=SourceType.GEOSPATIAL,
            summary=(
                f"The route was checked against "
                f"{restricted_zone.name}. "
                f"Final distance is "
                f"{route_distance_km} km."
            ),
            observed_at=(
                generated_at
                - timedelta(minutes=5)
            ),
            retrieved_at=generated_at,
            freshness_minutes=5,
            confidence=0.91,
        )

        risk_factor = RiskFactor(
            code="GEOFENCE_ROUTE_RISK",
            label="Route and geofence conditions",
            level=risk_level,
            score=risk_score,
            explanation=explanation,
        )

        return GISAgentOutput(
            route=route,
            crosses_restricted_zone=(
                final_route_intersects
            ),
            geofence_names=[
                restricted_zone.name
            ],
            risk_factor=risk_factor,
            evidence=[evidence],
        )