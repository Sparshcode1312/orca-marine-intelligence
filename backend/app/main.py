from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.config import get_settings

from app.api.trips import router as trips_router


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Database connections and external API clients will be
    # initialized here in later steps.
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Evidence-grounded marine decision-support API.",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
    ],
)


app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    trips_router,
    prefix=settings.api_v1_prefix,
)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "running",
        "health": f"{settings.api_v1_prefix}/health",
    }