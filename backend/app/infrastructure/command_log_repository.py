from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import CommandLogRow


CommandStatus = Literal["success", "failed", "rejected"]


class CommandLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(
        self,
        *,
        command_type: str,
        device_id: UUID,
        payload: dict[str, Any],
        status: CommandStatus,
        error_message: str | None = None,
    ) -> CommandLogRow:
        row = CommandLogRow(
            command_type=command_type,
            device_id=device_id,
            payload=payload,
            status=status,
            error_message=error_message,
        )
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return row

    def list_recent(self, limit: int = 50) -> list[CommandLogRow]:
        if not 1 <= limit <= 200:
            raise ValueError("Limit must be between 1 and 200.")

        statement = (
            select(CommandLogRow)
            .order_by(
                CommandLogRow.created_at.desc(),
                CommandLogRow.id.desc(),
            )
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())