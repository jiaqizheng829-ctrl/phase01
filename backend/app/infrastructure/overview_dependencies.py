from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.automation.service import AutomationService
from app.application.overview.facade import LocationOverviewFacade
from app.infrastructure.automation_context_repository import (
    AutomationContextRepository,
)
from app.infrastructure.automation_repository import AutomationRepository
from app.infrastructure.db import get_session
from app.infrastructure.overview_repository import OverviewRepository


def get_overview_facade(
    session: Session = Depends(get_session),
) -> LocationOverviewFacade:
    rules = AutomationRepository(session)

    automation = AutomationService(
        rules=rules,
        contexts=AutomationContextRepository(session),
    )

    return LocationOverviewFacade(
        overview=OverviewRepository(session),
        rules=rules,
        automation=automation,
    )