from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.actuator_execution_repository import (
    ActuatorExecutionRepository,
)
from app.infrastructure.adapters.actuators.factory import (
    build_actuator_port,
)
from app.infrastructure.adapters.actuators.max_run_time import utc_now
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

        self.actuator = build_actuator_port(
            self.adapter,
            self.repository.load_state,
            self.repository.save_log,
            clock=clock,
        )

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        self.repository.load_state(device_id)
        self.actuator.apply(device_id, command, payload)