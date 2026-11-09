from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActuatorExecutionDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    success: bool
    policy_applied: list[str]
    message: str | None
    created_at: datetime