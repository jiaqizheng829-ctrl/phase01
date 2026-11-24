from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import AlertRow


AlertSeverity = Literal["info", "warning", "critical"]


class AlertRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(
        self,
        *,
        device_id: UUID | None,
        location_id: UUID | None,
        zone_id: UUID | None,
        severity: AlertSeverity,
        message: str,
        event_type: str,
    ) -> AlertRow:
        row = AlertRow(
            device_id=device_id,
            location_id=location_id,
            zone_id=zone_id,
            severity=severity,
            message=message,
            event_type=event_type,
            status="active",
        )
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return row

    def list_recent(
        self,
        *,
        status: str = "active",
        since: datetime | None = None,
        location_id: UUID | None = None,
        zone_id: UUID | None = None,
        limit: int = 50,
    ) -> list[AlertRow]:
        if status not in {"active", "resolved", "all"}:
            raise ValueError(
                "Status must be active, resolved, or all."
            )

        if not 1 <= limit <= 200:
            raise ValueError("Limit must be between 1 and 200.")

        statement = select(AlertRow)

        if status != "all":
            statement = statement.where(AlertRow.status == status)

        if since is not None:
            statement = statement.where(AlertRow.created_at >= since)

        if location_id is not None:
            statement = statement.where(
                AlertRow.location_id == location_id
            )

        if zone_id is not None:
            statement = statement.where(AlertRow.zone_id == zone_id)

        statement = statement.order_by(
            AlertRow.created_at.desc(),
            AlertRow.id.desc(),
        ).limit(limit)

        return list(self.session.scalars(statement).all())