from typing import Protocol
from uuid import UUID

from app.application.devices.state_dto import ActuatorStateDto
from app.domain.actuators.context import ActuatorContext


class ActuatorStateStore(Protocol):
    def get_state(self, device_id: UUID) -> str:
        ...

    def get_state_for_update(self, device_id: UUID) -> str:
        ...

    def save_state(self, device_id: UUID, state: str) -> None:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


class ActuatorStateService:
    def __init__(self, repository: ActuatorStateStore) -> None:
        self.repository = repository

    def get_state(self, device_id: UUID) -> ActuatorStateDto:
        context = ActuatorContext(
            self.repository.get_state(device_id)
        )
        return self._to_dto(device_id, context)

    def transition(
        self,
        device_id: UUID,
        target: str,
    ) -> ActuatorStateDto:
        try:
            current = self.repository.get_state_for_update(device_id)
            context = ActuatorContext(current)

            # Domain validation happens before any state is saved.
            context.transition(target)

            self.repository.save_state(device_id, context.state)
            result = self._to_dto(device_id, context)
            self.repository.commit()
            return result
        except Exception:
            self.repository.rollback()
            raise

    @staticmethod
    def _to_dto(
        device_id: UUID,
        context: ActuatorContext,
    ) -> ActuatorStateDto:
        return ActuatorStateDto(
            device_id=device_id,
            state=context.state,
            allowed_commands=context.allowed_commands(),
        )