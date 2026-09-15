from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import add_scalar_reference

from app.infrastructure.settings import settings
from app.interfaces.api.health import router as health_router
from app.interfaces.api.sensors import router as sensors_router

app = FastAPI(
    title="Greenhouse API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
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
add_scalar_reference(app, route="/scalar")


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "Greenhouse API is running",
        "api_reference": "/scalar",
        "openapi": "/openapi.json",
    }
