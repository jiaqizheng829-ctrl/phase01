from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: Literal["sensor", "actuator"]
    device_family: str
    display_name: str
    default_config: dict[str, Any]
    zone_id: UUID | None = None
    location_id: UUID | None = None
    state: Literal[
        "off",
        "idle",
        "running",
        "error",
        "maintenance",
    ] | None = None
    allowed_commands: list[str] = Field(default_factory=list)


class ZoneAssignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zone_id: UUID | None