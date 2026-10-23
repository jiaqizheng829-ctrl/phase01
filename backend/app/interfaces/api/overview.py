from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.application.overview.dto import LocationOverviewDto
from app.application.overview.facade import (
    LocationOverviewFacade,
    OverviewLocationNotFoundError,
)
from app.infrastructure.overview_dependencies import get_overview_facade


router = APIRouter(
    prefix="/api/locations",
    tags=["overview"],
)


@router.get(
    "/{location_id}/overview",
    response_model=LocationOverviewDto,
)
def get_location_overview(
    location_id: UUID,
    facade: LocationOverviewFacade = Depends(get_overview_facade),
) -> LocationOverviewDto:
    try:
        return facade.get_overview(location_id)
    except OverviewLocationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc