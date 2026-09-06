from fastapi import APIRouter, HTTPException, status

from app.db import check_database_connection


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    if not check_database_connection():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "db": "unavailable"},
        )

    return {"status": "ok", "db": "ok"}
