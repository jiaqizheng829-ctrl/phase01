from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.application.devices.state_dto import ActuatorStateDto
from app.domain.actuators.context import ActuatorContext
from app.domain.events.bus import EventBus
from app.domain.events.events import ActuatorStateChanged


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
    def __init__(
        self,
        repository: ActuatorStateStore,
        *,
        bus: EventBus | None = None,
        load_assignment: Callable[
            [UUID], tuple[UUID | None, UUID | None]
        ] | None = None,
    ) -> None:
        if bus is not None and load_assignment is None:
            raise ValueError(
                "load_assignment is required when an event bus is supplied."
            )

        self.repository = repository
        self.bus = bus
        self.load_assignment = load_assignment

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
        event = None

        try:
            current = self.repository.get_state_for_update(device_id)
            context = ActuatorContext(current)

            # Validate before saving or preparing a notification.
            context.transition(target)

            if self.bus is not None and self.load_assignment is not None:
                location_id, zone_id = self.load_assignment(device_id)

                if zone_id is None:
                    location_id = None

                event = ActuatorStateChanged(
                    device_id=device_id,
                    location_id=location_id,
                    zone_id=zone_id,
                    state=context.state,
                )

            self.repository.save_state(device_id, context.state)
            result = self._to_dto(device_id, context)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise

        # Failed saves or commits must not publish a state-change event.
        if event is not None and self.bus is not None:
            self.bus.publish(event)

        return result

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