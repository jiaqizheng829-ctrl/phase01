from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StateTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: str


class ActuatorStateDto(BaseModel):
    device_id: UUID
    state: Literal["off", "idle", "running", "error", "maintenance"]
    allowed_commands: list[str]