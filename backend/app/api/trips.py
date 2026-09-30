import asyncio

from fastapi import APIRouter, status

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
from app.schemas.decision import IntelligenceDecision
from app.schemas.trip import (
    TripAnalysisRequest,
    TripValidationResponse,
)
from app.orchestration.workflow import ORCAWorkflow


router = APIRouter(
    prefix="/trips",
    tags=["Trip Intelligence"],
)


planner_agent = PlannerAgent()
weather_agent = WeatherAgent()
ocean_agent = OceanAgent()
pfz_agent = PFZAgent()
gis_agent = GISAgent()
safety_agent = SafetyAgent()
orca_workflow = ORCAWorkflow()
   
@router.post(
    "/validate",
    response_model=TripValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate a marine trip request",
)
async def validate_trip_request(
    request: TripAnalysisRequest,
) -> TripValidationResponse:
    return TripValidationResponse(
        accepted=True,
        message="Trip request passed ORCA input validation.",
        request=request,
    )


@router.post(
    "/analyze",
    response_model=IntelligenceDecision,
    status_code=status.HTTP_200_OK,
    summary="Generate a complete multi-agent marine intelligence decision",
)
async def analyze_trip(
    request: TripAnalysisRequest,
) -> IntelligenceDecision:
    """
    Coordinate all ORCA specialist agents and return one explainable
    marine intelligence decision.
    """

    return await orca_workflow.run(request)


@router.post(
    "/plan",
    response_model=PlannerOutput,
    status_code=status.HTTP_200_OK,
    summary="Select specialist agents for a trip request",
)
async def plan_trip(
    request: TripAnalysisRequest,
) -> PlannerOutput:
    return await planner_agent.run(request)


@router.post(
    "/agents/weather",
    response_model=WeatherAgentOutput,
    status_code=status.HTTP_200_OK,
    summary="Run the prototype Weather Agent",
)
async def run_weather_agent(
    request: TripAnalysisRequest,
) -> WeatherAgentOutput:
    return await weather_agent.run(request)


@router.post(
    "/agents/ocean",
    response_model=OceanAgentOutput,
    status_code=status.HTTP_200_OK,
    summary="Run the prototype Ocean Agent",
)
async def run_ocean_agent(
    request: TripAnalysisRequest,
) -> OceanAgentOutput:
    return await ocean_agent.run(request)


@router.post(
    "/agents/pfz",
    response_model=PFZAgentOutput,
    status_code=status.HTTP_200_OK,
    summary="Run the prototype PFZ Agent",
)
async def run_pfz_agent(
    request: TripAnalysisRequest,
) -> PFZAgentOutput:
    return await pfz_agent.run(request)


@router.post(
    "/agents/gis",
    response_model=GISAgentOutput,
    status_code=status.HTTP_200_OK,
    summary="Run the prototype PFZ and GIS agents",
)
async def run_gis_agent(
    request: TripAnalysisRequest,
) -> GISAgentOutput:
    pfz_output = await pfz_agent.run(request)

    selected_zone = next(
        zone
        for zone in pfz_output.candidate_zones
        if zone.zone_id == pfz_output.selected_zone_id
    )

    gis_input = GISAgentInput(
        request=request,
        selected_zone=selected_zone,
    )

    return await gis_agent.run(gis_input)


@router.post(
    "/agents/safety",
    response_model=SafetyAgentOutput,
    status_code=status.HTTP_200_OK,
    summary="Run the complete prototype marine safety assessment",
)
async def run_safety_agent(
    request: TripAnalysisRequest,
) -> SafetyAgentOutput:
    """
    Run independent specialist agents concurrently, calculate the
    route and produce an explainable final safety assessment.
    """

    weather_output, ocean_output, pfz_output = await asyncio.gather(
        weather_agent.run(request),
        ocean_agent.run(request),
        pfz_agent.run(request),
    )

    selected_zone = next(
        zone
        for zone in pfz_output.candidate_zones
        if zone.zone_id == pfz_output.selected_zone_id
    )

    gis_output = await gis_agent.run(
        GISAgentInput(
            request=request,
            selected_zone=selected_zone,
        )
    )

    safety_input = SafetyAgentInput(
        request=request,
        weather=weather_output,
        ocean=ocean_output,
        gis=gis_output,
    )

    return await safety_agent.run(safety_input)