from typing import TypedDict

from app.agents.contracts import (
    AgentError,
    GISAgentOutput,
    OceanAgentOutput,
    PFZAgentOutput,
    PlannerOutput,
    SafetyAgentOutput,
    WeatherAgentOutput,
)
from app.schemas.decision import (
    AgentExecution,
    EvidenceItem,
    IntelligenceDecision,
    RiskFactor,
)
from app.schemas.trip import TripAnalysisRequest


class ORCAState(TypedDict, total=False):
    """
    Shared state passed through the ORCA multi-agent workflow.

    total=False allows specialist outputs to be added gradually
    as each agent completes its task.
    """

    request: TripAnalysisRequest

    planner_output: PlannerOutput
    weather_output: WeatherAgentOutput
    ocean_output: OceanAgentOutput
    pfz_output: PFZAgentOutput
    gis_output: GISAgentOutput
    safety_output: SafetyAgentOutput

    combined_risk_factors: list[RiskFactor]
    combined_evidence: list[EvidenceItem]
    agent_executions: list[AgentExecution]

    errors: list[AgentError]

    final_decision: IntelligenceDecision