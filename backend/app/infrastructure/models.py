from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.infrastructure.base import Base


class LocationRow(Base):
    __tablename__ = "locations"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class ZoneRow(Base):
    __tablename__ = "zones"
    __table_args__ = (
        UniqueConstraint(
            "location_id", "name",
            name="uq_zones_location_name",
        ),
        CheckConstraint(
            "moisture_threshold_low >= 0 "
            "AND moisture_threshold_high <= 1 "
            "AND moisture_threshold_low < moisture_threshold_high",
            name="ck_zones_moisture_thresholds",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    location_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    moisture_threshold_low: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    moisture_threshold_high: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    schedule: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )


class DeviceRow(Base):
    __tablename__ = "devices"
    __table_args__ = (
        Index("ix_devices_role", "role"),
        Index("ix_devices_family", "device_family"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    device_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'sensor'"),
    )
    device_family: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'simulation'"),
    )
    display_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    default_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    zone_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("zones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    location_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )