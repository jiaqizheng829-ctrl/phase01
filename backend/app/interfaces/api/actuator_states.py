from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.devices.state_dto import (
    ActuatorStateDto,
    StateTransitionRequest,
)
from app.application.devices.state_service import ActuatorStateService
from app.domain.actuators.state import IllegalTransitionError
from app.infrastructure.actuator_state_repository import (
    ActuatorNotFoundError,
    ActuatorStateRepository,
)
from app.infrastructure.db import get_session


router = APIRouter(
    prefix="/api/devices",
    tags=["actuator states"],
)


def get_state_service(
    session: Session = Depends(get_session),
) -> ActuatorStateService:
    return ActuatorStateService(
        ActuatorStateRepository(session)
    )


@router.get(
    "/{device_id}/state",
    response_model=ActuatorStateDto,
)
def get_actuator_state(
    device_id: UUID,
    service: ActuatorStateService = Depends(get_state_service),
) -> ActuatorStateDto:
    try:
        return service.get_state(device_id)
    except ActuatorNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post(
    "/{device_id}/transition",
    response_model=ActuatorStateDto,
)
def transition_actuator(
    device_id: UUID,
    payload: StateTransitionRequest,
    service: ActuatorStateService = Depends(get_state_service),
) -> ActuatorStateDto:
    try:
        return service.transition(device_id, payload.target)
    except ActuatorNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except IllegalTransitionError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc