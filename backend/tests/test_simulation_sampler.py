from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.application.readings.sampler import (
    SamplingDevice,
    SimulationSampler,
)
from app.application.readings.service import ReadingIngest
from app.domain.devices.entity import Device
from app.domain.sensors.reading import Reading
from app.infrastructure.adapters.sensors.selector import (
    select_sensor_adapter,
)


START = datetime(2026, 10, 1, tzinfo=timezone.utc)


def make_device(protocol="simulation", role="sensor"):
    return Device(
        id=uuid4(),
        device_type=(
            "moisture_sensor" if role == "sensor" else "water_pump"
        ),
        role=role,
        device_family=(
            "simulation" if protocol == "simulation" else "edge"
        ),
        display_name="Sampler test",
        default_config={"protocol": protocol},
    )


class FakeDevices:
    def __init__(self, settings):
        self.settings = settings

    def list_sampling_devices(self):
        return self.settings

    def get(self, device_id):
        return next(
            (
                item.device
                for item in self.settings
                if item.device.id == device_id
            ),
            None,
        )


class FakeReadings:
    def __init__(self):
        self.rows = []

    def insert(self, reading):
        self.rows.append(reading)
        return reading

    def list_for_device(self, device_id, limit=20):
        rows = [
            reading
            for reading in self.rows
            if reading.device_id == device_id
        ]
        return sorted(
            rows,
            key=lambda reading: reading.recorded_at,
            reverse=True,
        )[:limit]

    def latest_for_device(self, device_id):
        rows = self.list_for_device(device_id, limit=1)
        return rows[0] if rows else None


def build_sampler(settings):
    devices = FakeDevices(settings)
    readings = FakeReadings()
    ingest = ReadingIngest(devices, readings, select_sensor_adapter)
    sampler = SimulationSampler(
        devices,
        readings,
        ingest,
        select_sensor_adapter,
    )
    return sampler, devices, readings, ingest


def test_sampler_respects_exact_interval():
    device = make_device()
    sampler, _, readings, _ = build_sampler(
        [SamplingDevice(device, 30, True)]
    )

    assert sampler.run_once(START) == 1
    assert sampler.run_once(START + timedelta(seconds=29)) == 0
    assert sampler.run_once(START + timedelta(seconds=30)) == 1

    assert [row.recorded_at for row in readings.rows] == [
        START,
        START + timedelta(seconds=30),
    ]


def test_sampler_skips_disabled_mqtt_and_actuators():
    enabled = make_device()
    disabled = make_device()
    mqtt = make_device(protocol="mqtt")
    actuator = make_device(role="actuator")

    sampler, _, readings, _ = build_sampler(
        [
            SamplingDevice(enabled, 30, True),
            SamplingDevice(disabled, 30, False),
            SamplingDevice(mqtt, 30, True),
            SamplingDevice(actuator, 30, True),
        ]
    )

    assert sampler.run_once(START) == 1
    assert [row.device_id for row in readings.rows] == [enabled.id]


def test_sampler_uses_each_devices_own_interval():
    fast = make_device()
    slow = make_device()

    sampler, _, readings, _ = build_sampler(
        [
            SamplingDevice(fast, 10, True),
            SamplingDevice(slow, 30, True),
        ]
    )

    assert sampler.run_once(START) == 2
    assert sampler.run_once(START + timedelta(seconds=10)) == 1

    assert len(readings.list_for_device(fast.id)) == 2
    assert len(readings.list_for_device(slow.id)) == 1


def test_sampler_uses_updated_interval():
    device = make_device()
    sampler, devices, readings, _ = build_sampler(
        [SamplingDevice(device, 30, True)]
    )

    assert sampler.run_once(START) == 1

    devices.settings[0] = replace(
        devices.settings[0],
        sampling_interval_seconds=10,
    )

    assert sampler.run_once(START + timedelta(seconds=10)) == 1
    assert len(readings.rows) == 2


def test_tracking_can_stop_and_resume_sampling():
    device = make_device()
    sampler, devices, readings, _ = build_sampler(
        [SamplingDevice(device, 30, True)]
    )

    assert sampler.run_once(START) == 1

    devices.settings[0] = replace(
        devices.settings[0],
        tracking_enabled=False,
    )
    assert sampler.run_once(START + timedelta(seconds=60)) == 0

    devices.settings[0] = replace(
        devices.settings[0],
        tracking_enabled=True,
    )
    assert sampler.run_once(START + timedelta(seconds=61)) == 1
    assert len(readings.rows) == 2


def test_manual_read_time_also_controls_next_sample():
    device = make_device()
    sampler, _, readings, ingest = build_sampler(
        [SamplingDevice(device, 30, True)]
    )

    ingest.record(
        device.id,
        Reading(
            device_id=device.id,
            value=0.4,
            unit="vwc",
            source="simulation",
            recorded_at=START,
        ),
    )

    assert sampler.run_once(START + timedelta(seconds=29)) == 0
    assert sampler.run_once(START + timedelta(seconds=30)) == 1
    assert len(readings.rows) == 2


def test_sampler_rejects_time_without_timezone():
    sampler, _, readings, _ = build_sampler(
        [SamplingDevice(make_device(), 30, True)]
    )

    with pytest.raises(ValueError, match="timezone"):
        sampler.run_once(datetime(2026, 10, 1))

    assert readings.rows == []