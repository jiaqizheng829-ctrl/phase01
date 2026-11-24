from collections.abc import Callable
from uuid import UUID

from app.domain.events.bus import EventBus
from app.domain.events.events import (
    ActuatorStateChanged,
    CommandFailed,
    ReadingCreated,
    ThresholdCrossed,
)


class MoistureThresholdSubscriber:
    def __init__(
        self,
        bus: EventBus,
        load_threshold: Callable[[UUID], float | None],
    ) -> None:
        self.bus = bus
        self.load_threshold = load_threshold

    def on_reading(self, event: ReadingCreated) -> None:
        if event.unit != "vwc" or event.zone_id is None:
            return

        threshold = self.load_threshold(event.zone_id)
        if threshold is None:
            return

        # Equality does not count as being below the threshold.
        if event.value < threshold:
            self.bus.publish(
                ThresholdCrossed(
                    device_id=event.device_id,
                    location_id=event.location_id,
                    zone_id=event.zone_id,
                    value=event.value,
                    threshold_low=threshold,
                )
            )


class AlertPersistenceSubscriber:
    def __init__(
        self,
        save_alert: Callable[..., object],
    ) -> None:
        self.save_alert = save_alert

    def on_threshold(self, event: ThresholdCrossed) -> None:
        self.save_alert(
            device_id=event.device_id,
            location_id=event.location_id,
            zone_id=event.zone_id,
            severity="warning",
            message="Moisture below zone low",
            event_type=event.event_type,
        )

    def on_command(self, event: CommandFailed) -> None:
        self.save_alert(
            device_id=event.device_id,
            location_id=event.location_id,
            zone_id=event.zone_id,
            severity="warning",
            message=event.message,
            event_type=event.event_type,
        )

    def on_state(self, event: ActuatorStateChanged) -> None:
        if event.state != "error":
            return

        self.save_alert(
            device_id=event.device_id,
            location_id=event.location_id,
            zone_id=event.zone_id,
            severity="critical",
            message="Actuator entered error",
            event_type=event.event_type,
        )