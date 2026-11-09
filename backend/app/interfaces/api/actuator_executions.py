from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.devices.execution_dto import ActuatorExecutionDto
from app.infrastructure.actuator_execution_repository import (
    ActuatorExecutionRepository,
)
from app.infrastructure.db import get_session


router = APIRouter(
    prefix="/api/actuators",
    tags=["actuator executions"],
)


@router.get(
    "/executions",
    response_model=list[ActuatorExecutionDto],
)
def list_actuator_executions(
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[ActuatorExecutionDto]:
    repository = ActuatorExecutionRepository(session)
    rows = repository.list_recent(limit)

    return [
        ActuatorExecutionDto.model_validate(row)
        for row in rows
    ]