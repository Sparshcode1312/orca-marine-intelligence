from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.agents.contracts import PFZAgentOutput
from app.schemas.decision import (
    AgentName,
    EvidenceItem,
    FishingZoneRecommendation,
    SourceType,
)
from app.schemas.trip import GeoPoint, TripAnalysisRequest
from app.utils.geo import calculate_distance_km


@dataclass(frozen=True)
class PrototypeZoneData:
    zone_id: str
    name: str
    latitude_offset: float
    longitude_offset: float
    sea_surface_temperature_c: float
    chlorophyll_mg_m3: float


class PFZAgent:
    """
    Generates and ranks prototype fishing zones.

    Official INCOIS PFZ and ISRO ocean-colour data will
    replace these prototype candidates later.
    """

    PROTOTYPE_ZONES = (
        PrototypeZoneData(
            zone_id="PFZ-PROTOTYPE-01",
            name="Near Coastal Candidate",
            latitude_offset=-0.08,
            longitude_offset=0.10,
            sea_surface_temperature_c=28.4,
            chlorophyll_mg_m3=1.2,
        ),
        PrototypeZoneData(
            zone_id="PFZ-PROTOTYPE-02",
            name="Central Opportunity Zone",
            latitude_offset=-0.13,
            longitude_offset=0.16,
            sea_surface_temperature_c=27.9,
            chlorophyll_mg_m3=1.7,
        ),
        PrototypeZoneData(
            zone_id="PFZ-PROTOTYPE-03",
            name="Outer Coastal Candidate",
            latitude_offset=-0.20,
            longitude_offset=0.24,
            sea_surface_temperature_c=29.1,
            chlorophyll_mg_m3=0.9,
        ),
    )

    @property
    def name(self) -> AgentName:
        return AgentName.PFZ

    @staticmethod
    def create_coordinate(
        origin: GeoPoint,
        latitude_offset: float,
        longitude_offset: float,
    ) -> GeoPoint:
        return GeoPoint(
            latitude=max(
                -89.5,
                min(
                    89.5,
                    origin.latitude + latitude_offset,
                ),
            ),
            longitude=max(
                -179.5,
                min(
                    179.5,
                    origin.longitude + longitude_offset,
                ),
            ),
        )

    @staticmethod
    def calculate_sst_score(
        temperature_c: float,
    ) -> float:
        target_temperature_c = 28.0

        return max(
            0,
            100
            - abs(
                temperature_c
                - target_temperature_c
            )
            * 25,
        )

    @staticmethod
    def calculate_chlorophyll_score(
        chlorophyll_mg_m3: float,
    ) -> float:
        return max(
            0,
            min(
                100,
                (chlorophyll_mg_m3 / 2.0) * 100,
            ),
        )

    @staticmethod
    def calculate_distance_score(
        distance_km: float,
        maximum_distance_km: float,
    ) -> float:
        distance_ratio = (
            distance_km
            / max(maximum_distance_km, 1)
        )

        if distance_ratio <= 1:
            return max(
                0,
                100 - distance_ratio * 60,
            )

        return max(
            0,
            40 - (distance_ratio - 1) * 80,
        )

    @classmethod
    def calculate_suitability_score(
        cls,
        temperature_c: float,
        chlorophyll_mg_m3: float,
        distance_km: float,
        maximum_distance_km: float,
    ) -> int:
        sst_score = cls.calculate_sst_score(
            temperature_c
        )

        chlorophyll_score = (
            cls.calculate_chlorophyll_score(
                chlorophyll_mg_m3
            )
        )

        distance_score = (
            cls.calculate_distance_score(
                distance_km,
                maximum_distance_km,
            )
        )

        suitability_score = round(
            sst_score * 0.35
            + chlorophyll_score * 0.40
            + distance_score * 0.25
        )

        return max(
            0,
            min(100, suitability_score),
        )

    async def run(
        self,
        request: TripAnalysisRequest,
    ) -> PFZAgentOutput:
        candidate_zones: list[
            FishingZoneRecommendation
        ] = []

        for zone_data in self.PROTOTYPE_ZONES:
            center = self.create_coordinate(
                origin=request.origin,
                latitude_offset=(
                    zone_data.latitude_offset
                ),
                longitude_offset=(
                    zone_data.longitude_offset
                ),
            )

            distance_km = calculate_distance_km(
                request.origin,
                center,
            )

            suitability_score = (
                self.calculate_suitability_score(
                    temperature_c=(
                        zone_data
                        .sea_surface_temperature_c
                    ),
                    chlorophyll_mg_m3=(
                        zone_data.chlorophyll_mg_m3
                    ),
                    distance_km=distance_km,
                    maximum_distance_km=(
                        request.max_distance_km
                    ),
                )
            )

            candidate_zones.append(
                FishingZoneRecommendation(
                    zone_id=zone_data.zone_id,
                    name=zone_data.name,
                    center=center,
                    suitability_score=(
                        suitability_score
                    ),
                    distance_km=distance_km,
                    recommended_from=(
                        request.planned_departure
                    ),
                    recommended_until=(
                        request.planned_departure
                        + timedelta(hours=6)
                    ),
                )
            )

        selected_zone = max(
            candidate_zones,
            key=lambda zone: (
                zone.suitability_score
            ),
        )

        generated_at = datetime.now(timezone.utc)

        evidence = [
            EvidenceItem(
                source_name="Prototype INCOIS PFZ Advisory",
                source_type=SourceType.ADVISORY,
                summary=(
                    "Prototype advisory identifies three "
                    "candidate fishing zones near the "
                    "selected departure location."
                ),
                observed_at=(
                    generated_at
                    - timedelta(minutes=42)
                ),
                retrieved_at=generated_at,
                freshness_minutes=42,
                confidence=0.84,
            ),
            EvidenceItem(
                source_name="Prototype ISRO Ocean Colour Feed",
                source_type=SourceType.SATELLITE,
                summary=(
                    "Prototype SST and chlorophyll values "
                    "were used to rank fishing suitability."
                ),
                observed_at=(
                    generated_at
                    - timedelta(hours=3)
                ),
                retrieved_at=generated_at,
                freshness_minutes=180,
                confidence=0.81,
            ),
        ]

        return PFZAgentOutput(
            candidate_zones=candidate_zones,
            selected_zone_id=selected_zone.zone_id,
            selection_reason=(
                f"{selected_zone.name} received the highest "
                f"prototype suitability score of "
                f"{selected_zone.suitability_score}/100 "
                f"after evaluating SST, chlorophyll and "
                f"distance from the vessel."
            ),
            evidence=evidence,
        )