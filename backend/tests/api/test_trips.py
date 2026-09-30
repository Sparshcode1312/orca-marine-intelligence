from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def build_trip_payload() -> dict:
    return {
        "query": (
            "Find a suitable fishing zone and check whether "
            "the complete trip is safe."
        ),
        "language": "en",
        "origin": {
            "latitude": 19.8135,
            "longitude": 85.8312,
        },
        "planned_departure": (
            datetime.now(timezone.utc) + timedelta(hours=3)
        ).isoformat(),
        "max_distance_km": 50,
        "vessel_type": "small_motorized",
        "crew_count": 4,
        "include_explanation": True,
    }


@pytest.mark.asyncio
async def test_analyze_trip_returns_complete_decision() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/trips/analyze",
            json=build_trip_payload(),
        )

    assert response.status_code == 200

    decision = response.json()

    assert decision["recommendation"] in {
        "proceed",
        "proceed_with_caution",
        "do_not_proceed",
    }

    assert decision["risk_level"] in {
        "low",
        "moderate",
        "high",
        "severe",
    }

    assert 0 <= decision["safety_score"] <= 100
    assert 0 <= decision["confidence"] <= 1

    assert decision["recommended_zone"] is not None
    assert decision["recommended_route"] is not None

    assert len(decision["risk_factors"]) >= 1
    assert len(decision["evidence"]) >= 1

    assert decision["prototype_data"] is True
    assert decision["human_verification_required"] is True


@pytest.mark.asyncio
async def test_all_agents_complete_successfully() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/trips/analyze",
            json=build_trip_payload(),
        )

    assert response.status_code == 200

    executions = response.json()["agent_executions"]

    expected_agents = {
        "planner",
        "weather",
        "ocean",
        "pfz",
        "gis",
        "safety",
    }

    returned_agents = {
        execution["agent"]
        for execution in executions
    }

    assert returned_agents == expected_agents

    assert all(
        execution["status"] == "succeeded"
        for execution in executions
    )


@pytest.mark.asyncio
async def test_past_departure_time_is_rejected() -> None:
    transport = ASGITransport(app=app)

    payload = build_trip_payload()

    payload["planned_departure"] = (
        datetime.now(timezone.utc) - timedelta(hours=2)
    ).isoformat()

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/trips/analyze",
            json=payload,
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_coordinates_are_rejected() -> None:
    transport = ASGITransport(app=app)

    payload = build_trip_payload()
    payload["origin"]["latitude"] = 150

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/trips/analyze",
            json=payload,
        )

    assert response.status_code == 422