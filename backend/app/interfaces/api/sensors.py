from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.application.sensor_service import SensorService
from app.infrastructure.db import get_session

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
