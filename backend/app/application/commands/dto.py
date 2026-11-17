from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_type: str
    device_id: UUID
    payload: dict[str, Any] = Field(default_factory=dict)


class CommandLogDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    command_type: str
    device_id: UUID
    payload: dict[str, Any]
    status: Literal["success", "failed", "rejected"]
    error_message: str | None
    created_at: datetime