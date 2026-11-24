from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.readings.service import ReadingIngest
from app.domain.devices.entity import Device
from app.domain.events.bus import EventBus
from app.domain.events.events import ReadingCreated
from app.domain.sensors.reading import Reading


class FakeDevices:
    def __init__(self, device):
        self.device = device

    def get(self, device_id):
        if device_id == self.device.id:
            return self.device
        return None


class FakeReadings:
    def __init__(self):
        self.rows = []

    def insert(self, reading):
        self.rows.append(reading)
        return reading

    def list_for_device(self, device_id, limit=20):
        return [
            row for row in self.rows
            if row.device_id == device_id
        ][:limit]


def make_device(assigned=True):
    return Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Test moisture sensor",
        default_config={},
        location_id=uuid4() if assigned else None,
        zone_id=uuid4() if assigned else None,
    )


def make_reading(device):
    return Reading(
        device_id=device.id,
        value=0.10,
        unit="vwc",
        source="simulation",
        recorded_at=datetime.now(timezone.utc),
    )


@pytest.mark.parametrize("tracking", [True, False])
def test_tracking_controls_publish_but_not_storage(tracking):
    device = make_device()
    reading = make_reading(device)
    readings = FakeReadings()
    bus = EventBus()
    received = []

    def observe(event):
        # Storage must complete before notification.
        assert readings.rows == [reading]
        received.append(event)

    bus.subscribe(ReadingCreated, observe)

    ingest = ReadingIngest(
        FakeDevices(device),
        readings,
        lambda device: None,
        bus=bus,
        is_tracking_enabled=lambda identifier: tracking,
    )
    ingest.record(device.id, reading)

    assert readings.rows == [reading]
    assert len(received) == (1 if tracking else 0)

    if tracking:
        event = received[0]
        assert event.device_id == device.id
        assert event.location_id == device.location_id
        assert event.zone_id == device.zone_id
        assert event.value == reading.value
        assert event.unit == reading.unit
        assert event.source == reading.source
        assert event.recorded_at == reading.recorded_at


def test_unassigned_reading_publishes_null_assignment():
    device = make_device(assigned=False)
    bus = EventBus()
    received = []
    bus.subscribe(ReadingCreated, received.append)

    ingest = ReadingIngest(
        FakeDevices(device),
        FakeReadings(),
        lambda device: None,
        bus=bus,
        is_tracking_enabled=lambda identifier: True,
    )
    ingest.record(device.id, make_reading(device))

    assert len(received) == 1
    assert received[0].location_id is None
    assert received[0].zone_id is None


def test_failed_insert_does_not_publish():
    class FailingReadings(FakeReadings):
        def insert(self, reading):
            raise RuntimeError("Insert failed")

    device = make_device()
    bus = EventBus()
    received = []
    bus.subscribe(ReadingCreated, received.append)

    ingest = ReadingIngest(
        FakeDevices(device),
        FailingReadings(),
        lambda device: None,
        bus=bus,
        is_tracking_enabled=lambda identifier: True,
    )

    with pytest.raises(RuntimeError, match="Insert failed"):
        ingest.record(device.id, make_reading(device))

    assert received == []


def test_take_reading_uses_record_and_publishes_once():
    device = make_device()
    reading = make_reading(device)
    readings = FakeReadings()
    bus = EventBus()
    received = []
    bus.subscribe(ReadingCreated, received.append)

    class FakeAdapter:
        def read(self, target):
            assert target.id == device.id
            return reading

    ingest = ReadingIngest(
        FakeDevices(device),
        readings,
        lambda device: FakeAdapter(),
        bus=bus,
        is_tracking_enabled=lambda identifier: True,
    )
    ingest.take_reading(device.id)

    assert readings.rows == [reading]
    assert len(received) == 1
    assert received[0].device_id == device.id