from collections.abc import Iterable

from app.agents.contracts import PlannerOutput
from app.schemas.decision import AgentName
from app.schemas.trip import TripAnalysisRequest


class PlannerAgent:
    """
    Selects the specialist agents required for a trip request.

    This first implementation is deterministic and does not
    depend on an LLM.
    """

    WEATHER_KEYWORDS = {
        "weather",
        "forecast",
        "rain",
        "rainfall",
        "storm",
        "cyclone",
        "wind",
        "visibility",
        "मौसम",
        "बारिश",
        "तूफान",
        "हवा",
        "ପାଣିପାଗ",
    }

    OCEAN_KEYWORDS = {
        "ocean",
        "sea",
        "wave",
        "waves",
        "tide",
        "current",
        "swell",
        "समुद्र",
        "लहर",
        "ज्वार",
        "तरंग",
        "ସମୁଦ୍ର",
    }

    PFZ_KEYWORDS = {
        "fish",
        "fishing",
        "catch",
        "pfz",
        "zone",
        "chlorophyll",
        "sst",
        "मछली",
        "मछुआरा",
        "मत्स्य",
        "मछली पकड़ने",
        "ମାଛ",
    }

    GIS_KEYWORDS = {
        "route",
        "distance",
        "location",
        "map",
        "geofence",
        "restricted",
        "boundary",
        "रास्ता",
        "मार्ग",
        "दूरी",
        "स्थान",
        "नक्शा",
        "ପଥ",
    }

    SAFETY_KEYWORDS = {
        "safe",
        "safety",
        "danger",
        "dangerous",
        "risk",
        "alert",
        "warning",
        "सुरक्षित",
        "खतरा",
        "जोखिम",
        "चेतावनी",
        "ସୁରକ୍ଷିତ",
    }

    @property
    def name(self) -> AgentName:
        return AgentName.PLANNER

    @staticmethod
    def contains_keyword(
        query: str,
        keywords: Iterable[str],
    ) -> bool:
        return any(
            keyword in query
            for keyword in keywords
        )

    async def run(
        self,
        request: TripAnalysisRequest,
    ) -> PlannerOutput:
        normalized_query = request.query.casefold()

        selected_agents: set[AgentName] = set()
        detected_categories: list[str] = []

        weather_requested = self.contains_keyword(
            normalized_query,
            self.WEATHER_KEYWORDS,
        )

        ocean_requested = self.contains_keyword(
            normalized_query,
            self.OCEAN_KEYWORDS,
        )

        pfz_requested = self.contains_keyword(
            normalized_query,
            self.PFZ_KEYWORDS,
        )

        gis_requested = self.contains_keyword(
            normalized_query,
            self.GIS_KEYWORDS,
        )

        safety_requested = self.contains_keyword(
            normalized_query,
            self.SAFETY_KEYWORDS,
        )

        if weather_requested:
            selected_agents.add(AgentName.WEATHER)
            detected_categories.append("weather")

        if ocean_requested:
            selected_agents.add(AgentName.OCEAN)
            detected_categories.append("ocean")

        if pfz_requested:
            selected_agents.add(AgentName.PFZ)
            detected_categories.append("fishing zone")

        if gis_requested:
            selected_agents.add(AgentName.GIS)
            detected_categories.append("route and location")

        if safety_requested:
            # A safety request must always evaluate weather,
            # ocean conditions and the proposed route.
            selected_agents.update(
                {
                    AgentName.WEATHER,
                    AgentName.OCEAN,
                    AgentName.GIS,
                }
            )

            detected_categories.append("safety")

        # Every trip analysis must pass through the Safety Agent.
        selected_agents.add(AgentName.SAFETY)

        # If the intent is too general, run the complete core workflow.
        if len(selected_agents) == 1:
            selected_agents.update(
                {
                    AgentName.WEATHER,
                    AgentName.OCEAN,
                    AgentName.PFZ,
                    AgentName.GIS,
                }
            )

            detected_categories.append(
                "general marine trip analysis"
            )

        # A fishing-zone request also requires route validation.
        if AgentName.PFZ in selected_agents:
            selected_agents.add(AgentName.GIS)

        execution_order = [
            AgentName.WEATHER,
            AgentName.OCEAN,
            AgentName.PFZ,
            AgentName.GIS,
            AgentName.SAFETY,
        ]

        ordered_agents = [
            agent
            for agent in execution_order
            if agent in selected_agents
        ]

        unique_categories = list(
            dict.fromkeys(detected_categories)
        )

        reasoning = (
            "The request contains "
            + ", ".join(unique_categories)
            + " intent. ORCA selected the required specialist "
            "agents and included the Safety Agent for final "
            "risk evaluation."
        )

        return PlannerOutput(
            selected_agents=ordered_agents,
            reasoning=reasoning,
        )