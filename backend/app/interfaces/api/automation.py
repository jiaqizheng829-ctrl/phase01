from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.automation.dto import (
    EvaluationDto,
    StrategySettingsDto,
    StrategyUpdateRequest,
)
from app.application.automation.service import (
    AutomationService,
    LocationNotFoundError,
    StrategyNotConfiguredError,
)
from app.domain.automation.strategy import UnknownStrategyError
from app.infrastructure.automation_context_repository import (
    AutomationContextRepository,
)
from app.infrastructure.automation_repository import AutomationRepository
from app.infrastructure.db import get_session


router = APIRouter(
    prefix="/api/locations",
    tags=["automation"],
)


def get_automation_service(
    session: Session = Depends(get_session),
) -> AutomationService:
    return AutomationService(
        rules=AutomationRepository(session),
        contexts=AutomationContextRepository(session),
    )


@router.get(
    "/{location_id}/automation",
    response_model=StrategySettingsDto,
)
def get_automation_settings(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),
) -> StrategySettingsDto:
    try:
        return service.get_settings(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put(
    "/{location_id}/automation",
    response_model=StrategySettingsDto,
)
def save_automation_settings(
    location_id: UUID,
    payload: StrategyUpdateRequest,
    service: AutomationService = Depends(get_automation_service),
) -> StrategySettingsDto:
    try:
        return service.save_settings(
            location_id,
            payload.strategy_key,
        )
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnknownStrategyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/{location_id}/automation/evaluate",
    response_model=EvaluationDto,
)
def evaluate_automation(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),
) -> EvaluationDto:
    try:
        return service.evaluate(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (UnknownStrategyError, StrategyNotConfiguredError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc