from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import DeviceRow


class SamplingRepository:
    def __init__(self, session: Session):
        self.session = session

    def update(
        self,
        device_id: UUID,
        interval: int,
        tracking_enabled: bool,
    ) -> tuple[UUID, int, bool] | None:
        try:
            statement = (
                select(DeviceRow)
                .where(DeviceRow.id == device_id)
                .with_for_update()
            )
            row = self.session.scalar(statement)

            if row is None:
                self.session.rollback()
                return None

            row.sampling_interval_seconds = interval
            row.tracking_enabled = tracking_enabled

            self.session.flush()
            result = (
                row.id,
                row.sampling_interval_seconds,
                row.tracking_enabled,
            )
            self.session.commit()
            return result
        except Exception:
            self.session.rollback()
            raise