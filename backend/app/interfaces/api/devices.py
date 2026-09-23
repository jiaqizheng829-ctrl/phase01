from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.application.devices.dto import DeviceDto
from app.application.devices.family_service import DeviceFamilyService
from app.application.devices.mappers import to_device_dto
from app.domain.devices.family_factory import UnknownDeviceFamily
from app.infrastructure.db import get_session
from app.infrastructure.device_repository import DeviceRepository


router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
)


def get_family_service(
    session: Session = Depends(get_session),
) -> DeviceFamilyService:
    return DeviceFamilyService(DeviceRepository(session))


@router.get("", response_model=list[DeviceDto])
def list_devices(
    family: str | None = None,
    role: Literal["sensor", "actuator"] | None = None,
    service: DeviceFamilyService = Depends(get_family_service),
) -> list[DeviceDto]:
    devices = service.list_devices(
        family=family,
        role=role,
    )
    return [to_device_dto(device) for device in devices]


@router.post(
    "/provision",
    response_model=list[DeviceDto],
    status_code=201,
)
def provision_devices(
    family: str = Query(
        ...,
        description="Device family: simulation or edge",
    ),
    service: DeviceFamilyService = Depends(get_family_service),
) -> list[DeviceDto]:
    try:
        devices = service.provision_family(family)
    except UnknownDeviceFamily as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return [to_device_dto(device) for device in devices]