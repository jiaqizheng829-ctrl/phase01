from fastapi import APIRouter

from app.infrastructure.db import check_database_connection


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    database_ok = check_database_connection()

    return {
        "status": "ok" if database_ok else "degraded",
        "db": "ok" if database_ok else "fail",
    }
