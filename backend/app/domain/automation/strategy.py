from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from app.domain.automation.context import LocationAutomationContext


@dataclass(frozen=True)
class Recommendation:
    action: Literal["irrigate", "wait"]
    reason: str


class AutomationStrategy(ABC):
    @abstractmethod
    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        raise NotImplementedError


def missing_reading_recommendation(
    context: LocationAutomationContext,
) -> Recommendation | None:
    if not context.has_moisture_sensor:
        return Recommendation(
            action="wait",
            reason="No moisture sensor is assigned to this zone.",
        )

    if context.latest_moisture is None:
        return Recommendation(
            action="wait",
            reason="No saved moisture reading is available for this zone.",
        )

    return None


class ConservativeMoistureStrategy(AutomationStrategy):
    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        missing = missing_reading_recommendation(context)
        if missing is not None:
            return missing

        moisture = context.latest_moisture
        assert moisture is not None
        threshold = context.moisture_threshold_low

        if moisture < threshold:
            return Recommendation(
                action="irrigate",
                reason=(
                    f"Moisture {moisture:.4f} is below the zone's "
                    f"lower threshold {threshold:.4f}."
                ),
            )

        return Recommendation(
            action="wait",
            reason=(
                f"Moisture {moisture:.4f} is at or above the zone's "
                f"lower threshold {threshold:.4f}."
            ),
        )


class AggressiveMoistureStrategy(AutomationStrategy):
    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        missing = missing_reading_recommendation(context)
        if missing is not None:
            return missing

        moisture = context.latest_moisture
        assert moisture is not None
        threshold = (
            context.moisture_threshold_low
            + context.moisture_threshold_high
        ) / 2

        if moisture < threshold:
            return Recommendation(
                action="irrigate",
                reason=(
                    f"Moisture {moisture:.4f} is below the zone's "
                    f"midpoint threshold {threshold:.4f}."
                ),
            )

        return Recommendation(
            action="wait",
            reason=(
                f"Moisture {moisture:.4f} is at or above the zone's "
                f"midpoint threshold {threshold:.4f}."
            ),
        )


class UnknownStrategyError(ValueError):
    pass


_STRATEGIES: dict[str, type[AutomationStrategy]] = {
    "conservative": ConservativeMoistureStrategy,
    "aggressive": AggressiveMoistureStrategy,
}


def get_strategy(strategy_key: str) -> AutomationStrategy:
    strategy_class = _STRATEGIES.get(strategy_key)

    if strategy_class is None:
        raise UnknownStrategyError(
            f"Unknown automation strategy: {strategy_key}"
        )

    return strategy_class()