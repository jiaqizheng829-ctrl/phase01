from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from app.domain.actuators.ports import ActuatorPort
from app.infrastructure.adapters.actuators.logging import LoggingDecorator
from app.infrastructure.adapters.actuators.max_run_time import (
    MaxRunTimeDecorator,
    utc_now,
)


def build_actuator_port(
    inner: ActuatorPort,
    load_state: Callable[[UUID], tuple[str, datetime]],
    save_log: Callable[[UUID, bool, list[str], str | None], None],
    *,
    clock: Callable[[], datetime] = utc_now,
) -> ActuatorPort:
    limited = MaxRunTimeDecorator(
        inner,
        load_state,
        clock=clock,
    )

    return LoggingDecorator(
        limited,
        save_log,
    )