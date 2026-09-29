from app.domain.locations.validation import validate_zone

from copy import deepcopy
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domain.locations.entity import Zone
from app.domain.locations.errors import ConfigurationError
from app.infrastructure.models import DeviceRow, LocationRow, ZoneRow


class ZoneRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, location_id: UUID, zone: Zone) -> Zone | None:
        try:
            # Lock the location while changing its zones.
            location = self.session.scalar(
                select(LocationRow)
                .where(LocationRow.id == location_id)
                .with_for_update()
            )

            if location is None:
                self.session.rollback()
                return None

            existing_id = self.session.scalar(
                select(ZoneRow.id).where(
                    ZoneRow.location_id == location_id,
                    ZoneRow.name == zone.name,
                )
            )

            if existing_id is not None:
                raise ConfigurationError(
                    f"Duplicate zone name: {zone.name}"
                )

            row = ZoneRow(
                location_id=location_id,
                name=zone.name,
                moisture_threshold_low=zone.moisture_threshold_low,
                moisture_threshold_high=zone.moisture_threshold_high,
                schedule=deepcopy(zone.schedule),
            )
            self.session.add(row)
            self.session.flush()

            saved_zone = self._to_zone(row)
            self.session.commit()
            return saved_zone

        except Exception:
            self.session.rollback()
            raise

    def update(
        self,
        location_id: UUID,
        zone_id: UUID,
        changes: dict,
    ) -> Zone | None:
        try:
            location = self.session.scalar(
                select(LocationRow)
                .where(LocationRow.id == location_id)
                .with_for_update()
            )

            if location is None:
                self.session.rollback()
                return None

            row = self.session.scalar(
                select(ZoneRow).where(
                    ZoneRow.id == zone_id,
                    ZoneRow.location_id == location_id,
                )
            )

            if row is None:
                self.session.rollback()
                return None

            if any(value is None for value in changes.values()):
                raise ConfigurationError(
                    "Zone fields must not be null."
                )

            name = changes.get("name", row.name)
            low = changes.get(
                "moisture_threshold_low",
                float(row.moisture_threshold_low),
            )
            high = changes.get(
                "moisture_threshold_high",
                float(row.moisture_threshold_high),
            )
            schedule = changes.get("schedule", row.schedule)

            name = validate_zone(name, low, high, schedule)

            duplicate_id = self.session.scalar(
                select(ZoneRow.id).where(
                    ZoneRow.location_id == location_id,
                    ZoneRow.name == name,
                    ZoneRow.id != zone_id,
                )
            )

            if duplicate_id is not None:
                raise ConfigurationError(
                    f"Duplicate zone name: {name}"
                )

            row.name = name
            row.moisture_threshold_low = low
            row.moisture_threshold_high = high
            row.schedule = deepcopy(schedule)

            self.session.flush()
            updated_zone = self._to_zone(row)
            self.session.commit()
            return updated_zone

        except Exception:
            self.session.rollback()
            raise

    def delete(self, location_id: UUID, zone_id: UUID) -> bool:
        try:
            location = self.session.scalar(
                select(LocationRow)
                .where(LocationRow.id == location_id)
                .with_for_update()
            )

            if location is None:
                self.session.rollback()
                return False

            zone = self.session.scalar(
                select(ZoneRow)
                .where(
                    ZoneRow.id == zone_id,
                    ZoneRow.location_id == location_id,
                )
                .with_for_update()
            )

            if zone is None:
                self.session.rollback()
                return False

            zone_count = self.session.scalar(
                select(func.count())
                .select_from(ZoneRow)
                .where(ZoneRow.location_id == location_id)
            )

            if zone_count <= 1:
                raise ConfigurationError(
                    "Cannot delete the last zone of a location."
                )

            self.session.execute(
                update(DeviceRow)
                .where(DeviceRow.zone_id == zone_id)
                .values(zone_id=None, location_id=None)
            )

            self.session.delete(zone)
            self.session.commit()
            return True

        except Exception:
            self.session.rollback()
            raise

    @staticmethod
    def _to_zone(row: ZoneRow) -> Zone:
        return Zone(
            id=row.id,
            name=row.name,
            moisture_threshold_low=float(row.moisture_threshold_low),
            moisture_threshold_high=float(row.moisture_threshold_high),
            schedule=deepcopy(row.schedule),
        )