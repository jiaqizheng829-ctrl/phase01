from app.application.devices.dto import DeviceDto
from app.application.locations.zone_assignment_service import (
    ZoneAssignmentService,
)
from app.infrastructure.zone_assignment_repository import (
    AssignmentNotFoundError,
    ZoneAssignmentRepository,
)

from app.application.locations.dto import ZoneUpdateRequest

from app.application.locations.dto import ZoneCreateRequest, ZoneRead
from app.application.locations.zone_service import ZoneService
from app.infrastructure.zone_repository import ZoneRepository

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.application.locations.config_service import (
    LocationConfigService,
    LocationNotFoundError,
)
from app.application.locations.dto import (
    LocationConfigCreateRequest,
    LocationConfigRead,
    LocationRead,
)
from app.domain.locations.errors import ConfigurationError
from app.infrastructure.db import get_session
from app.infrastructure.location_repository import LocationRepository


router = APIRouter(
    prefix="/api/locations",
    tags=["locations"],
)


def get_config_service(
    session: Session = Depends(get_session),
) -> LocationConfigService:
    return LocationConfigService(LocationRepository(session))


@router.post(
    "/config",
    response_model=LocationConfigRead,
    status_code=201,
)
def create_config(
    request: LocationConfigCreateRequest,
    service: LocationConfigService = Depends(get_config_service),
) -> LocationConfigRead:
    try:
        return service.create(request)
    except ConfigurationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get(
    "/{location_id}/config",
    response_model=LocationConfigRead,
)
def get_config(
    location_id: UUID,
    service: LocationConfigService = Depends(get_config_service),
) -> LocationConfigRead:
    try:
        return service.get(location_id)
    except LocationNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
@router.get(
    "",
    response_model=list[LocationRead],
    description="List all locations, newest first.",
)
def list_locations(
    service: LocationConfigService = Depends(get_config_service),
) -> list[LocationRead]:
    return service.list_locations()
@router.delete(
    "/{location_id}",
    status_code=204,
    response_class=Response,
)
def delete_location(
    location_id: UUID,
    service: LocationConfigService = Depends(get_config_service),
) -> Response:
    try:
        service.delete(location_id)
    except LocationNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return Response(status_code=204)

def get_zone_service(
    session: Session = Depends(get_session),
) -> ZoneService:
    return ZoneService(ZoneRepository(session))


@router.post(
    "/{location_id}/zones",
    response_model=ZoneRead,
    status_code=201,
)
def add_zone(
    location_id: UUID,
    request: ZoneCreateRequest,
    service: ZoneService = Depends(get_zone_service),
) -> ZoneRead:
    try:
        return service.add(location_id, request)
    except LocationNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ConfigurationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

@router.patch(
    "/{location_id}/zones/{zone_id}",
    response_model=ZoneRead,
)
def update_zone(
    location_id: UUID,
    zone_id: UUID,
    request: ZoneUpdateRequest,
    service: ZoneService = Depends(get_zone_service),
) -> ZoneRead:
    try:
        return service.update(location_id, zone_id, request)
    except LocationNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ConfigurationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

@router.delete(
    "/{location_id}/zones/{zone_id}",
    status_code=204,
    response_class=Response,
)
def delete_zone(
    location_id: UUID,
    zone_id: UUID,
    service: ZoneService = Depends(get_zone_service),
) -> Response:
    try:
        service.delete(location_id, zone_id)
    except LocationNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ConfigurationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return Response(status_code=204)

def get_assignment_service(
    session: Session = Depends(get_session),
) -> ZoneAssignmentService:
    return ZoneAssignmentService(ZoneAssignmentRepository(session))


@router.get(
    "/{location_id}/zones/{zone_id}/devices",
    response_model=list[DeviceDto],
)
def list_zone_devices(
    location_id: UUID,
    zone_id: UUID,
    service: ZoneAssignmentService = Depends(get_assignment_service),
) -> list[DeviceDto]:
    try:
        return service.list_devices(location_id, zone_id)
    except AssignmentNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error