from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlertDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID | None
    zone_id: UUID | None
    device_id: UUID | None
    severity: Literal["info", "warning", "critical"]
    message: str
    event_type: str
    status: Literal["active", "resolved"]
    created_at: datetime