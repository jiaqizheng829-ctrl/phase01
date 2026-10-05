from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.application.readings.dto import ReadingDto
from app.application.readings.service import (
    DeviceNotFoundError,
    ReadingIngest,
)
from app.application.sensor_service import SensorService
from app.domain.sensors.reading import ReadingError
from app.infrastructure.adapters.sensors.selector import (
    select_sensor_adapter,
)
from app.infrastructure.db import get_session
from app.infrastructure.device_repository import DeviceRepository
from app.infrastructure.reading_repository import ReadingRepository


router = APIRouter(prefix="/api/sensors", tags=["sensors"])


class CreateSensorRequest(BaseModel):
    type: str = Field(
        ...,
        examples=["moisture"],
        description="Supported types: moisture or light",
    )
    display_name: str | None = Field(default=None, max_length=128)


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    display_name: str
    default_config: dict[str, Any]
    sampling_interval_seconds: int
    tracking_enabled: bool


def get_reading_service(
    session: Session = Depends(get_session),
) -> ReadingIngest:
    return ReadingIngest(
        devices=DeviceRepository(session),
        readings=ReadingRepository(session),
        select_adapter=select_sensor_adapter,
    )


@router.get("", response_model=list[SensorResponse])
def list_sensors(session: Session = Depends(get_session)):
    return SensorService(session).list_sensors()


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor(
    payload: CreateSensorRequest,
    session: Session = Depends(get_session),
):
    try:
        return SensorService(session).create_sensor(
            sensor_type=payload.type,
            display_name=payload.display_name,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "/{device_id}/read",
    response_model=ReadingDto,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Device or adapter cannot produce a reading"},
        404: {"description": "Device not found"},
    },
)
def read_sensor(
    device_id: UUID,
    service: ReadingIngest = Depends(get_reading_service),
):
    try:
        return service.take_reading(device_id)
    except DeviceNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ReadingError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get(
    "/{device_id}/readings",
    response_model=list[ReadingDto],
    responses={
        400: {"description": "Invalid sensor or history limit"},
        404: {"description": "Device not found"},
    },
)
def list_sensor_readings(
    device_id: UUID,
    limit: int = 20,
    service: ReadingIngest = Depends(get_reading_service),
):
    try:
        return service.list_readings(device_id, limit=limit)
    except DeviceNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ReadingError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error