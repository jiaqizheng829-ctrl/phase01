"""sensor_readings

Revision ID: 3b45041792c3
Revises: 16f6a0abd449
"""

from alembic import op
import sqlalchemy as sa


revision = "3b45041792c3"
down_revision = "16f6a0abd449"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sensor_readings",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_sensor_readings_device_recorded_at",
        "sensor_readings",
        ["device_id", sa.literal_column("recorded_at DESC")],
        unique=False,
    )

    op.add_column(
        "devices",
        sa.Column(
            "sampling_interval_seconds",
            sa.Integer(),
            server_default=sa.text("300"),
            nullable=False,
        ),
    )
    op.add_column(
        "devices",
        sa.Column(
            "tracking_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )

    # Copy numeric intervals from the old JSON configuration.
    # Round fractions up and clamp values to the supported integer range.
    # Missing or non-numeric values keep the default of 300 seconds.
    op.execute(
        """
        UPDATE devices
        SET sampling_interval_seconds =
            CASE
                WHEN jsonb_typeof(
                    default_config -> 'sampling_interval_seconds'
                ) = 'number'
                THEN LEAST(
                    2147483647::numeric,
                    GREATEST(
                        5::numeric,
                        CEIL(
                            (
                                default_config
                                ->> 'sampling_interval_seconds'
                            )::numeric
                        )
                    )
                )::integer
                ELSE 300
            END
        """
    )

    op.create_check_constraint(
        "ck_devices_sampling_interval",
        "devices",
        "sampling_interval_seconds >= 5",
    )


def downgrade():
    op.drop_constraint(
        "ck_devices_sampling_interval",
        "devices",
        type_="check",
    )
    op.drop_column("devices", "tracking_enabled")
    op.drop_column("devices", "sampling_interval_seconds")
    op.drop_index(
        "ix_sensor_readings_device_recorded_at",
        table_name="sensor_readings",
    )
    op.drop_table("sensor_readings")