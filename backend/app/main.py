from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import add_scalar_reference

from app.api.health import router as health_router


app = FastAPI(
    title="Greenhouse API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
add_scalar_reference(app, route="/scalar")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Greenhouse API is running"}
