from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.application.alerts.dto import AlertDto
from app.infrastructure.alert_repository import AlertRepository
from app.infrastructure.db import get_session


router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get(
    "",
    response_model=list[AlertDto],
    responses={
        400: {"description": "Invalid alert status."},
    },
)
def list_alerts(
    status: str = Query(
        default="active",
        description="active, resolved, or all",
    ),
    since: datetime | None = Query(
        default=None,
        description=(
            "Include alerts created at or after this timestamp. "
            "Timestamps without a timezone are interpreted as UTC."
        ),
    ),
    location_id: UUID | None = None,
    zone_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[AlertDto]:
    """List persisted alerts, newest first, with optional filters."""
    if status not in {"active", "resolved", "all"}:
        raise HTTPException(
            status_code=400,
            detail="Status must be active, resolved, or all.",
        )

    if since is not None and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    rows = AlertRepository(session).list_recent(
        status=status,
        since=since,
        location_id=location_id,
        zone_id=zone_id,
        limit=limit,
    )

    return [AlertDto.model_validate(row) for row in rows]