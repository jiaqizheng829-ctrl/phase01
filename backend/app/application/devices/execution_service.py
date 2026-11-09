from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.actuator_execution_repository import (
    ActuatorExecutionRepository,
)
from app.infrastructure.adapters.actuators.logging import (
    LoggingDecorator,
)
from app.infrastructure.adapters.actuators.max_run_time import (
    MaxRunTimeDecorator,
    utc_now,
)
from app.infrastructure.adapters.actuators.simulation import (
    SimulationActuatorAdapter,
)


class ActuatorExecutionService:
    def __init__(
        self,
        session: Session,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.repository = ActuatorExecutionRepository(session)

        self.adapter = SimulationActuatorAdapter()

        limited = MaxRunTimeDecorator(
            self.adapter,
            self.repository.load_state,
            clock=clock,
        )

        self.actuator = LoggingDecorator(
            limited,
            self.repository.save_log,
        )

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        # Reject missing devices and sensors before execution.
        self.repository.load_state(device_id)

        # Logging wraps the runtime check so blocked attempts are saved.
        self.actuator.apply(device_id, command, payload)