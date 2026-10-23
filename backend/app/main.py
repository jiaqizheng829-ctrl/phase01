import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import add_scalar_reference

from app.infrastructure.sampling_runner import run_sampling_loop
from app.infrastructure.settings import settings
from app.interfaces.api.health import router as health_router
from app.interfaces.api.sensors import router as sensors_router
from app.interfaces.api.devices import router as devices_router
from app.interfaces.api.locations import router as locations_router
from app.interfaces.api.automation import router as automation_router
from app.interfaces.api.overview import router as overview_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # API tests use a separate test database and drive the sampler directly.
    # Do not start a background sampler against the normal database in tests.
    sampler_enabled = (
        os.environ.get("SIMULATION_SAMPLER_ENABLED", "true").lower()
        in {"true", "1", "yes"}
        and not os.environ.get("TEST_DATABASE_URL")
    )

    stop = asyncio.Event()
    task = None

    if sampler_enabled:
        task = asyncio.create_task(run_sampling_loop(stop))

    try:
        yield
    finally:
        stop.set()
        if task is not None:
            await task


app = FastAPI(
    title="Greenhouse API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(sensors_router)
app.include_router(devices_router)
app.include_router(locations_router)
app.include_router(automation_router)
app.include_router(overview_router)
add_scalar_reference(app, route="/scalar")


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "Greenhouse API is running",
        "api_reference": "/scalar",
        "openapi": "/openapi.json",
    }