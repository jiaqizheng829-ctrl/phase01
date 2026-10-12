from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StrategyUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_key: str


class StrategySettingsDto(BaseModel):
    location_id: UUID
    strategy_key: str | None


class ZoneRecommendationDto(BaseModel):
    zone_id: UUID
    latest_moisture: float | None
    moisture_threshold_low: float
    moisture_threshold_high: float
    action: Literal["irrigate", "wait"]
    reason: str


class EvaluationDto(BaseModel):
    location_id: UUID
    strategy_key: str
    action: Literal["irrigate", "wait"]
    reason: str
    zones: list[ZoneRecommendationDto]