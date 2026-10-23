from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.overview.dto import (
    LatestReadingDto,
    LocationSummaryDto,
    OverviewDeviceDto,
    OverviewZoneDto,
)
from app.infrastructure.models import (
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)


class OverviewRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_location_with_zones(
        self,
        location_id: UUID,
    ) -> tuple[LocationSummaryDto, list[OverviewZoneDto]] | None:
        statement = (
            select(LocationRow, ZoneRow)
            .outerjoin(
                ZoneRow,
                ZoneRow.location_id == LocationRow.id,
            )
            .where(LocationRow.id == location_id)
            .order_by(ZoneRow.name, ZoneRow.id)
        )
        rows = self.session.execute(statement).all()

        if not rows:
            return None

        location = rows[0][0]
        summary = LocationSummaryDto(
            id=location.id,
            name=location.name,
        )

        zones = [
            OverviewZoneDto(
                id=zone.id,
                name=zone.name,
                moisture_threshold_low=float(
                    zone.moisture_threshold_low
                ),
                moisture_threshold_high=float(
                    zone.moisture_threshold_high
                ),
            )
            for _, zone in rows
            if zone is not None
        ]

        return summary, zones

    def list_assigned_devices(
        self,
        location_id: UUID,
    ) -> list[tuple[UUID, OverviewDeviceDto]]:
        statement = (
            select(DeviceRow)
            .join(ZoneRow, ZoneRow.id == DeviceRow.zone_id)
            .where(
                DeviceRow.location_id == location_id,
                DeviceRow.zone_id.is_not(None),
                ZoneRow.location_id == location_id,
            )
            .order_by(DeviceRow.display_name, DeviceRow.id)
        )
        devices = self.session.scalars(statement).all()

        return [
            (
                device.zone_id,
                OverviewDeviceDto(
                    id=device.id,
                    device_type=device.device_type,
                    role=device.role,
                    display_name=device.display_name,
                ),
            )
            for device in devices
        ]

    def latest_readings_for_devices(
        self,
        device_ids: list[UUID],
    ) -> list[LatestReadingDto]:
        if not device_ids:
            return []

        ranked = (
            select(
                ReadingRow.device_id,
                ReadingRow.value,
                ReadingRow.unit,
                ReadingRow.recorded_at,
                func.row_number()
                .over(
                    partition_by=ReadingRow.device_id,
                    order_by=(
                        ReadingRow.recorded_at.desc(),
                        ReadingRow.id.desc(),
                    ),
                )
                .label("reading_rank"),
            )
            .where(ReadingRow.device_id.in_(device_ids))
            .subquery()
        )

        statement = (
            select(
                ranked.c.device_id,
                ranked.c.value,
                ranked.c.unit,
                ranked.c.recorded_at,
                DeviceRow.tracking_enabled,
                DeviceRow.sampling_interval_seconds,
            )
            .join(
                DeviceRow,
                DeviceRow.id == ranked.c.device_id,
            )
            .where(ranked.c.reading_rank == 1)
            .order_by(ranked.c.device_id)
        )

        rows = self.session.execute(statement).mappings().all()

        return [
            LatestReadingDto(
                device_id=row["device_id"],
                value=float(row["value"]),
                unit=row["unit"],
                recorded_at=row["recorded_at"],
                tracking_enabled=row["tracking_enabled"],
                sampling_interval_seconds=row[
                    "sampling_interval_seconds"
                ],
            )
            for row in rows
        ]