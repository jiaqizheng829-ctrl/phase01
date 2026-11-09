from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    DeviceRow,
)


class ActuatorExecutionNotFoundError(ValueError):
    pass


class ActuatorExecutionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def load_state(self, device_id: UUID) -> tuple[str, datetime]:
        device = self.session.get(DeviceRow, device_id)

        if device is None or device.role != "actuator":
            raise ActuatorExecutionNotFoundError(
                f"Actuator '{device_id}' was not found."
            )

        state = self.session.get(ActuatorStateRow, device_id)

        if state is None:
            raise RuntimeError(
                f"State is missing for actuator '{device_id}'."
            )

        return state.state, state.updated_at

    def save_log(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> None:
        row = ActuatorExecutionLogRow(
            device_id=device_id,
            success=success,
            policy_applied=list(policy_applied),
            message=message,
        )

        try:
            self.session.add(row)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def list_recent(
        self,
        limit: int = 20,
    ) -> list[ActuatorExecutionLogRow]:
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100.")

        statement = (
            select(ActuatorExecutionLogRow)
            .order_by(
                ActuatorExecutionLogRow.created_at.desc(),
                ActuatorExecutionLogRow.id.desc(),
            )
            .limit(limit)
        )

        return list(self.session.scalars(statement).all())