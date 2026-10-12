from typing import Protocol
from uuid import UUID

from app.application.automation.dto import (
    EvaluationDto,
    StrategySettingsDto,
    ZoneRecommendationDto,
)
from app.domain.automation.context import LocationAutomationContext
from app.domain.automation.strategy import get_strategy


class LocationNotFoundError(LookupError):
    pass


class StrategyNotConfiguredError(ValueError):
    pass


class AutomationRuleStore(Protocol):
    def location_exists(self, location_id: UUID) -> bool:
        ...

    def get_strategy_key(self, location_id: UUID) -> str | None:
        ...

    def save_strategy_key(
        self,
        location_id: UUID,
        strategy_key: str,
    ) -> str:
        ...


class AutomationContextStore(Protocol):
    def list_for_location(
        self,
        location_id: UUID,
    ) -> list[LocationAutomationContext]:
        ...


class AutomationService:
    def __init__(
        self,
        rules: AutomationRuleStore,
        contexts: AutomationContextStore,
    ) -> None:
        self.rules = rules
        self.contexts = contexts

    def _require_location(self, location_id: UUID) -> None:
        if not self.rules.location_exists(location_id):
            raise LocationNotFoundError("Location not found.")

    def get_settings(self, location_id: UUID) -> StrategySettingsDto:
        self._require_location(location_id)

        return StrategySettingsDto(
            location_id=location_id,
            strategy_key=self.rules.get_strategy_key(location_id),
        )

    def save_settings(
        self,
        location_id: UUID,
        strategy_key: str,
    ) -> StrategySettingsDto:
        self._require_location(location_id)

        # Validate before writing anything to the database.
        get_strategy(strategy_key)

        saved_key = self.rules.save_strategy_key(
            location_id,
            strategy_key,
        )

        return StrategySettingsDto(
            location_id=location_id,
            strategy_key=saved_key,
        )

    def evaluate(self, location_id: UUID) -> EvaluationDto:
        self._require_location(location_id)

        strategy_key = self.rules.get_strategy_key(location_id)

        if strategy_key is None:
            raise StrategyNotConfiguredError(
                "Save an automation strategy before evaluating."
            )

        strategy = get_strategy(strategy_key)
        contexts = self.contexts.list_for_location(location_id)

        zones: list[ZoneRecommendationDto] = []

        for context in contexts:
            recommendation = strategy.decide(context)

            zones.append(
                ZoneRecommendationDto(
                    zone_id=context.zone_id,
                    latest_moisture=context.latest_moisture,
                    moisture_threshold_low=(
                        context.moisture_threshold_low
                    ),
                    moisture_threshold_high=(
                        context.moisture_threshold_high
                    ),
                    action=recommendation.action,
                    reason=recommendation.reason,
                )
            )

        irrigation_count = sum(
            zone.action == "irrigate" for zone in zones
        )

        if not zones:
            reason = "This location has no zones."
        else:
            reason = (
                f"{irrigation_count} of {len(zones)} zones "
                "recommend irrigation. See individual zone results."
            )

        return EvaluationDto(
            location_id=location_id,
            strategy_key=strategy_key,
            action="irrigate" if irrigation_count else "wait",
            reason=reason,
            zones=zones,
        )