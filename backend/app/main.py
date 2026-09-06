from fastapi import FastAPI
from scalar_fastapi import add_scalar_reference

from app.api.health import router as health_router


app = FastAPI(
    title="Greenhouse API",
    version="0.1.0",
)

app.include_router(health_router)
add_scalar_reference(app, route="/scalar")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Greenhouse API is running"}
