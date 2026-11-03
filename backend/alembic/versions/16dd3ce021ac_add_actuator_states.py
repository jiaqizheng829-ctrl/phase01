"""add actuator states

Revision ID: 16dd3ce021ac
Revises: 9d391b40fb2f
"""

from alembic import op
import sqlalchemy as sa


revision = "16dd3ce021ac"
down_revision = "9d391b40fb2f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "actuator_states",
        sa.Column(
            "device_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "state",
            sa.String(length=32),
            server_default=sa.text("'idle'"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('off', 'idle', 'running', 'error', 'maintenance')",
            name="ck_actuator_states_state",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("device_id"),
    )

    # Initialize existing actuators only. Sensors have no actuator state.
    op.execute(
        sa.text(
            """
            INSERT INTO actuator_states (device_id, state)
            SELECT id, 'idle'
            FROM devices
            WHERE role = 'actuator'
            """
        )
    )


def downgrade():
    op.drop_table("actuator_states")