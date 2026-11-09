from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from app.domain.actuators.ports import ActuatorPort


class MaxRunTimeExceededError(ValueError):
    def __init__(self) -> None:
        super().__init__("Max run time exceeded")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MaxRunTimeDecorator(ActuatorPort):
    def __init__(
        self,
        inner: ActuatorPort,
        load_state: Callable[[UUID], tuple[str, datetime]],
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.inner = inner
        self.load_state = load_state
        self.clock = clock

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        state, updated_at = self.load_state(device_id)

        if state == "running":
            now = self.clock()

            if (
                now.utcoffset() is None
                or updated_at.utcoffset() is None
            ):
                raise ValueError("Timestamps must include a timezone.")

            if now - updated_at >= timedelta(minutes=30):
                raise MaxRunTimeExceededError()

        self.inner.apply(device_id, command, payload)