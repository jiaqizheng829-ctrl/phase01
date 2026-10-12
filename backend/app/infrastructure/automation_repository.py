from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.infrastructure.models import AutomationRuleRow, LocationRow


class AutomationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def location_exists(self, location_id: UUID) -> bool:
        statement = select(LocationRow.id).where(
            LocationRow.id == location_id
        )
        return self.session.scalar(statement) is not None

    def get_strategy_key(self, location_id: UUID) -> str | None:
        statement = select(AutomationRuleRow.strategy_key).where(
            AutomationRuleRow.location_id == location_id
        )
        return self.session.scalar(statement)

    def save_strategy_key(
        self,
        location_id: UUID,
        strategy_key: str,
    ) -> str:
        statement = (
            insert(AutomationRuleRow)
            .values(
                location_id=location_id,
                strategy_key=strategy_key,
            )
            .on_conflict_do_update(
                constraint="uq_automation_rules_location_id",
                set_={
                    "strategy_key": strategy_key,
                    "updated_at": func.now(),
                },
            )
            .returning(AutomationRuleRow.strategy_key)
        )

        try:
            saved_key = self.session.execute(statement).scalar_one()
            self.session.commit()
            return saved_key
        except Exception:
            self.session.rollback()
            raise