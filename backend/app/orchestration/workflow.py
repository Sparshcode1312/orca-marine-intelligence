import asyncio
from datetime import datetime, timezone
from typing import Awaitable, TypeVar

from app.agents.contracts import (
    GISAgentInput,
    GISAgentOutput,
    OceanAgentOutput,
    PFZAgentOutput,
    PlannerOutput,
    SafetyAgentInput,
    SafetyAgentOutput,
    WeatherAgentOutput,
)
from app.agents.gis import GISAgent
from app.agents.ocean import OceanAgent
from app.agents.pfz import PFZAgent
from app.agents.planner import PlannerAgent
from app.agents.safety import SafetyAgent
from app.agents.weather import WeatherAgent
from app.schemas.decision import (
    AgentExecution,
    AgentName,
    AgentStatus,
    EvidenceItem,
    IntelligenceDecision,
)
from app.schemas.trip import TripAnalysisRequest


AgentResult = TypeVar("AgentResult")


class ORCAWorkflow:
    """
    Central orchestrator for the ORCA multi-agent intelligence system.

    It runs independent agents concurrently, manages dependent agents,
    records execution metadata and produces one final decision.
    """

    def __init__(self) -> None:
        self._planner = PlannerAgent()
        self._weather = WeatherAgent()
        self._ocean = OceanAgent()
        self._pfz = PFZAgent()
        self._gis = GISAgent()
        self._safety = SafetyAgent()

    async def run(
        self,
        request: TripAnalysisRequest,
    ) -> IntelligenceDecision:
        executions: list[AgentExecution] = []

        planner_output = await self._run_and_track(
            agent_name=AgentName.PLANNER,
            operation=self._planner.run(request),
            executions=executions,
        )

        weather_result, ocean_result, pfz_result = await asyncio.gather(
            self._run_and_track(
                agent_name=AgentName.WEATHER,
                operation=self._weather.run(request),
                executions=executions,
            ),
            self._run_and_track(
                agent_name=AgentName.OCEAN,
                operation=self._ocean.run(request),
                executions=executions,
            ),
            self._run_and_track(
                agent_name=AgentName.PFZ,
                operation=self._pfz.run(request),
                executions=executions,
            ),
        )

        weather_output: WeatherAgentOutput = weather_result
        ocean_output: OceanAgentOutput = ocean_result
        pfz_output: PFZAgentOutput = pfz_result

        selected_zone = next(
            zone
            for zone in pfz_output.candidate_zones
            if zone.zone_id == pfz_output.selected_zone_id
        )

        gis_output: GISAgentOutput = await self._run_and_track(
            agent_name=AgentName.GIS,
            operation=self._gis.run(
                GISAgentInput(
                    request=request,
                    selected_zone=selected_zone,
                )
            ),
            executions=executions,
        )

        safety_output: SafetyAgentOutput = await self._run_and_track(
            agent_name=AgentName.SAFETY,
            operation=self._safety.run(
                SafetyAgentInput(
                    request=request,
                    weather=weather_output,
                    ocean=ocean_output,
                    gis=gis_output,
                )
            ),
            executions=executions,
        )

        combined_evidence = self._combine_evidence(
            safety_evidence=safety_output.evidence,
            pfz_evidence=pfz_output.evidence,
        )

        return IntelligenceDecision(
            request_id=request.request_id,
            recommendation=safety_output.recommendation,
            risk_level=safety_output.risk_level,
            safety_score=safety_output.safety_score,
            confidence=safety_output.confidence,
            summary=safety_output.summary,
            reasons=safety_output.reasons,
            alerts=safety_output.alerts,
            risk_factors=safety_output.risk_factors,
            evidence=combined_evidence,
            agent_executions=self._sort_executions(executions),
            recommended_zone=selected_zone,
            recommended_route=gis_output.route,
            prototype_data=True,
            human_verification_required=True,
        )

    @staticmethod
    async def _run_and_track(
        agent_name: AgentName,
        operation: Awaitable[AgentResult],
        executions: list[AgentExecution],
    ) -> AgentResult:
        started_at = datetime.now(timezone.utc)

        try:
            result = await operation
        except Exception:
            completed_at = datetime.now(timezone.utc)

            executions.append(
                AgentExecution(
                    agent=agent_name,
                    status=AgentStatus.FAILED,
                    started_at=started_at,
                    completed_at=completed_at,
                    evidence_count=0,
                    error_code="AGENT_EXECUTION_FAILED",
                )
            )

            raise

        completed_at = datetime.now(timezone.utc)

        evidence = getattr(result, "evidence", [])

        executions.append(
            AgentExecution(
                agent=agent_name,
                status=AgentStatus.SUCCEEDED,
                started_at=started_at,
                completed_at=completed_at,
                evidence_count=len(evidence),
            )
        )

        return result

    @staticmethod
    def _combine_evidence(
        safety_evidence: list[EvidenceItem],
        pfz_evidence: list[EvidenceItem],
    ) -> list[EvidenceItem]:
        combined: list[EvidenceItem] = []
        seen_items: set[tuple[str, str]] = set()

        for item in [*safety_evidence, *pfz_evidence]:
            identity = (
                item.source_name,
                item.summary,
            )

            if identity in seen_items:
                continue

            seen_items.add(identity)
            combined.append(item)

            if len(combined) == 50:
                break

        return combined

    @staticmethod
    def _sort_executions(
        executions: list[AgentExecution],
    ) -> list[AgentExecution]:
        execution_order = {
            AgentName.PLANNER: 0,
            AgentName.WEATHER: 1,
            AgentName.OCEAN: 2,
            AgentName.PFZ: 3,
            AgentName.GIS: 4,
            AgentName.SAFETY: 5,
        }

        return sorted(
            executions,
            key=lambda execution: execution_order[execution.agent],
        )