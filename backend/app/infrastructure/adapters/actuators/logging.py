from collections.abc import Callable
from typing import Any
from uuid import UUID

from app.domain.actuators.ports import ActuatorPort
from app.infrastructure.adapters.actuators.max_run_time import (
    MaxRunTimeExceededError,
)


class LoggingDecorator(ActuatorPort):
    def __init__(
        self,
        inner: ActuatorPort,
        save_log: Callable[
            [UUID, bool, list[str], str | None],
            None,
        ],
    ) -> None:
        self.inner = inner
        self.save_log = save_log

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        try:
            self.inner.apply(device_id, command, payload)
        except MaxRunTimeExceededError as exc:
            self.save_log(
                device_id,
                False,
                ["maxRunTime", "logging"],
                str(exc),
            )
            raise
        except Exception as exc:
            self.save_log(
                device_id,
                False,
                ["logging"],
                str(exc),
            )
            raise
        else:
            self.save_log(
                device_id,
                True,
                ["logging"],
                None,
            )