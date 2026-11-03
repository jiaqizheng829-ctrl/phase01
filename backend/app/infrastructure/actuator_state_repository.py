from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import ActuatorStateRow, DeviceRow


class ActuatorNotFoundError(LookupError):
    pass


class ActuatorStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_state(self, device_id: UUID) -> str:
        device = self.session.get(DeviceRow, device_id)

        if device is None or device.role != "actuator":
            raise ActuatorNotFoundError("Actuator not found.")

        row = self.session.get(ActuatorStateRow, device_id)

        if row is None:
            raise RuntimeError(
                f"State is missing for actuator {device_id}."
            )

        return row.state

    def get_state_for_update(self, device_id: UUID) -> str:
        # Lock the device while the service validates and saves a transition.
        device = self.session.scalar(
            select(DeviceRow)
            .where(
                DeviceRow.id == device_id,
                DeviceRow.role == "actuator",
            )
            .with_for_update()
        )

        if device is None:
            raise ActuatorNotFoundError("Actuator not found.")

        row = self.session.scalar(
            select(ActuatorStateRow)
            .where(ActuatorStateRow.device_id == device_id)
            .with_for_update()
        )

        if row is None:
            raise RuntimeError(
                f"State is missing for actuator {device_id}."
            )

        return row.state

    def save_state(self, device_id: UUID, state: str) -> None:
        # The application service must validate the transition first
        # and hold the lock obtained by get_state_for_update().
        row = self.session.get(ActuatorStateRow, device_id)

        if row is None:
            raise RuntimeError(
                f"State is missing for actuator {device_id}."
            )

        row.state = state
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()