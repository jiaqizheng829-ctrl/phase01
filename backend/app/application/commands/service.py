from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.application.commands.dto import CommandLogDto, CommandRequest
from app.domain.actuators.context import ActuatorContext
from app.domain.actuators.ports import ActuatorPort
from app.domain.commands.invoker import CommandInvoker
from app.domain.events.bus import EventBus
from app.domain.events.events import ActuatorStateChanged, CommandFailed
from app.infrastructure.actuator_execution_repository import (
    ActuatorExecutionRepository,
)
from app.infrastructure.actuator_state_repository import (
    ActuatorStateRepository,
)
from app.infrastructure.adapters.actuators.factory import build_actuator_port
from app.infrastructure.adapters.actuators.max_run_time import utc_now
from app.infrastructure.adapters.actuators.simulation import (
    SimulationActuatorAdapter,
)
from app.infrastructure.command_log_repository import (
    CommandLogRepository,
    CommandStatus,
)
from app.infrastructure.models import ActuatorExecutionLogRow, DeviceRow


class CommandService:
    def __init__(
        self,
        session: Session,
        *,
        adapter: ActuatorPort | None = None,
        clock: Callable[[], datetime] = utc_now,
        bus: EventBus | None = None,
    ) -> None:
        self.session = session
        self.bus = bus
        self.states = ActuatorStateRepository(session)
        self.logs = CommandLogRepository(session)
        self.executions = ActuatorExecutionRepository(session)
        self.invoker = CommandInvoker()
        self.adapter = (
            adapter if adapter is not None else SimulationActuatorAdapter()
        )
        self.port = build_actuator_port(
            self.adapter,
            self.executions.load_state,
            self._save_execution_log,
            clock=clock,
        )

    def _save_execution_log(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> None:
        self.session.add(
            ActuatorExecutionLogRow(
                device_id=device_id,
                success=success,
                policy_applied=list(policy_applied),
                message=message,
            )
        )

    def _finish(
        self,
        request: CommandRequest,
        status: CommandStatus,
        error_message: str | None = None,
    ) -> CommandLogDto:
        row = self.logs.add(
            command_type=request.command_type,
            device_id=request.device_id,
            payload=dict(request.payload),
            status=status,
            error_message=error_message,
        )
        result = CommandLogDto.model_validate(row)
        self.session.commit()
        return result

    def execute(self, request: CommandRequest) -> CommandLogDto:
        pending_events: list[object] = []

        try:
            result = self._execute(request, pending_events)
        except Exception:
            self.session.rollback()
            raise

        # Publish only after the command transaction has committed.
        if self.bus is not None:
            for event in pending_events:
                self.bus.publish(event)

        return result

    def _execute(
        self,
        request: CommandRequest,
        pending_events: list[object],
    ) -> CommandLogDto:
        saved_state = self.states.get_state_for_update(request.device_id)
        device = self.session.get(DeviceRow, request.device_id)

        if device is None:
            raise RuntimeError("The locked actuator could not be loaded.")

        # Capture assignment before commit expires ORM attributes.
        zone_id = device.zone_id
        location_id = device.location_id if zone_id is not None else None

        command = self.invoker.create(
            request.command_type,
            request.device_id,
            request.payload,
        )

        context = ActuatorContext(
            saved_state,
            device_type=device.device_type,
        )

        if request.command_type not in context.allowed_commands():
            return self._finish(
                request,
                "rejected",
                (
                    f"Command '{request.command_type}' is not allowed for "
                    f"'{device.device_type}' in state '{saved_state}'."
                ),
            )

        try:
            self.invoker.execute(command, self.port)
        except SQLAlchemyError:
            raise
        except Exception as exc:
            message = str(exc)
            pending_events.append(
                CommandFailed(
                    device_id=request.device_id,
                    location_id=location_id,
                    zone_id=zone_id,
                    command_type=request.command_type,
                    message=message,
                )
            )
            return self._finish(request, "failed", message)

        if command.target_state != context.state:
            context.transition(command.target_state)
            self.states.save_state(request.device_id, context.state)
            pending_events.append(
                ActuatorStateChanged(
                    device_id=request.device_id,
                    location_id=location_id,
                    zone_id=zone_id,
                    state=context.state,
                )
            )

        return self._finish(request, "success")

    def list_recent(self, limit: int = 50) -> list[CommandLogDto]:
        return [
            CommandLogDto.model_validate(row)
            for row in self.logs.list_recent(limit)
        ]