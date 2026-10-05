from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.sensors.reading import Reading
from app.infrastructure.models import ReadingRow


class ReadingRepository:
    def __init__(self, session: Session):
        self.session = session

    def insert(self, reading: Reading) -> Reading:
        row = ReadingRow(
            device_id=reading.device_id,
            value=Decimal(str(reading.value)),
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )

        try:
            self.session.add(row)
            self.session.flush()
            saved = self._to_reading(row)
            self.session.commit()
            return saved
        except Exception:
            self.session.rollback()
            raise

    def list_for_device(
        self,
        device_id: UUID,
        limit: int = 20,
    ) -> list[Reading]:
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100.")

        statement = (
            select(ReadingRow)
            .where(ReadingRow.device_id == device_id)
            .order_by(
                ReadingRow.recorded_at.desc(),
                ReadingRow.id.desc(),
            )
            .limit(limit)
        )

        rows = self.session.scalars(statement).all()
        return [self._to_reading(row) for row in rows]

    def latest_for_device(self, device_id: UUID) -> Reading | None:
        readings = self.list_for_device(device_id, limit=1)
        return readings[0] if readings else None

    @staticmethod
    def _to_reading(row: ReadingRow) -> Reading:
        return Reading(
            device_id=row.device_id,
            value=float(row.value),
            unit=row.unit,
            source=row.source,
            recorded_at=row.recorded_at,
        )