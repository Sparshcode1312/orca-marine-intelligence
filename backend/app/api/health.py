from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings


router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    timestamp: datetime


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API availability",
)
async def get_health() -> HealthResponse:
    settings = get_settings()

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc),
    )