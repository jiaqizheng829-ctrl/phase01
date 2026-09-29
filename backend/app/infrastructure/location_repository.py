from copy import deepcopy
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.locations.entity import Location, LocationConfig, Zone
from app.infrastructure.models import LocationRow, ZoneRow


class LocationRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, config: LocationConfig) -> LocationConfig:
        try:
            location_row = LocationRow(name=config.location.name)
            self.session.add(location_row)

            # Obtain the location ID without committing.
            self.session.flush()

            zone_rows = []

            for zone in config.location.zones:
                zone_row = ZoneRow(
                    location_id=location_row.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    schedule=deepcopy(zone.schedule),
                )
                self.session.add(zone_row)
                zone_rows.append(zone_row)

            # Send all zone inserts and obtain their IDs.
            self.session.flush()

            saved_config = self._to_config(location_row, zone_rows)

            # Commit the location and all zones together.
            self.session.commit()
            return saved_config

        except Exception:
            self.session.rollback()
            raise

    def get(self, location_id: UUID) -> LocationConfig | None:
        location_row = self.session.get(LocationRow, location_id)

        if location_row is None:
            return None

        statement = (
            select(ZoneRow)
            .where(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name, ZoneRow.id)
        )
        zone_rows = self.session.scalars(statement).all()

        return self._to_config(location_row, zone_rows)

    def list_locations(self) -> list[Location]:
        statement = select(LocationRow).order_by(
            LocationRow.created_at.desc(),
            LocationRow.id.desc(),
        )
        rows = self.session.scalars(statement).all()

        return [
            Location(
                id=row.id,
                name=row.name,
                zones=(),
            )
            for row in rows
        ]

    def delete(self, location_id: UUID) -> bool:
        try:
            location_row = self.session.get(LocationRow, location_id)

            if location_row is None:
                return False

            self.session.delete(location_row)
            self.session.commit()
            return True

        except Exception:
            self.session.rollback()
            raise

    @staticmethod
    def _to_config(
        location_row: LocationRow,
        zone_rows: list[ZoneRow],
    ) -> LocationConfig:
        zones = tuple(
            Zone(
                id=row.id,
                name=row.name,
                moisture_threshold_low=float(row.moisture_threshold_low),
                moisture_threshold_high=float(row.moisture_threshold_high),
                schedule=deepcopy(row.schedule),
            )
            for row in zone_rows
        )

        return LocationConfig(
            location=Location(
                id=location_row.id,
                name=location_row.name,
                zones=zones,
            )
        )