from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.domain.actuators.ports import ActuatorPort
from app.infrastructure.adapters.actuators.logging import LoggingDecorator
from app.infrastructure.adapters.actuators.max_run_time import (
    MaxRunTimeDecorator,
    MaxRunTimeExceededError,
)
from app.infrastructure.adapters.actuators.simulation import (
    SimulationActuatorAdapter,
)


NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def build_chain(state, elapsed):
    adapter = SimulationActuatorAdapter()
    logs = []

    def load_state(device_id):
        return state, NOW - elapsed

    def save_log(device_id, success, policies, message):
        logs.append({
            "device_id": device_id,
            "success": success,
            "policies": policies,
            "message": message,
        })

    limited = MaxRunTimeDecorator(
        adapter,
        load_state,
        clock=lambda: NOW,
    )
    decorated = LoggingDecorator(limited, save_log)
    return decorated, adapter, logs


@pytest.mark.parametrize(
    "elapsed",
    [
        timedelta(0),
        timedelta(minutes=29, seconds=59),
        timedelta(minutes=30) - timedelta(microseconds=1),
    ],
)
def test_running_below_limit_succeeds(elapsed):
    decorated, adapter, logs = build_chain("running", elapsed)
    device_id = uuid4()
    payload = {"duration_seconds": 10}

    decorated.apply(device_id, "start", payload)

    assert adapter.commands == [{
        "device_id": device_id,
        "command": "start",
        "payload": payload,
    }]
    assert logs == [{
        "device_id": device_id,
        "success": True,
        "policies": ["logging"],
        "message": None,
    }]


@pytest.mark.parametrize(
    "elapsed",
    [
        timedelta(minutes=30),
        timedelta(minutes=30, microseconds=1),
        timedelta(hours=2),
    ],
)
def test_runtime_limit_blocks_and_logs_failure(elapsed):
    decorated, adapter, logs = build_chain("running", elapsed)
    device_id = uuid4()

    with pytest.raises(
        MaxRunTimeExceededError,
        match="^Max run time exceeded$",
    ):
        decorated.apply(device_id, "start", {})

    assert adapter.commands == []
    assert logs == [{
        "device_id": device_id,
        "success": False,
        "policies": ["maxRunTime", "logging"],
        "message": "Max run time exceeded",
    }]


@pytest.mark.parametrize(
    "state",
    ["idle", "off", "error", "maintenance"],
)
def test_old_non_running_state_is_not_blocked(state):
    decorated, adapter, logs = build_chain(
        state,
        timedelta(days=1),
    )

    decorated.apply(uuid4(), "demo_command", {})

    assert len(adapter.commands) == 1
    assert len(logs) == 1
    assert logs[0]["success"] is True


def test_unknown_command_is_forwarded():
    decorated, adapter, logs = build_chain(
        "idle",
        timedelta(0),
    )

    decorated.apply(uuid4(), "unknown_command", {"value": 1})

    assert adapter.commands[0]["command"] == "unknown_command"
    assert logs[0]["success"] is True


def test_adapter_failure_is_logged_and_reraised():
    class FailingAdapter(ActuatorPort):
        def apply(self, device_id, command, payload):
            raise RuntimeError("Adapter failed")

    logs = []
    decorated = LoggingDecorator(
        FailingAdapter(),
        lambda *entry: logs.append(entry),
    )
    device_id = uuid4()

    with pytest.raises(RuntimeError, match="Adapter failed"):
        decorated.apply(device_id, "start", {})

    assert logs == [
        (device_id, False, ["logging"], "Adapter failed")
    ]


def test_success_log_is_written_after_execution():
    events = []

    class RecordingAdapter(ActuatorPort):
        def apply(self, device_id, command, payload):
            events.append("executed")

    def save_log(device_id, success, policies, message):
        events.append("logged")

    decorated = LoggingDecorator(RecordingAdapter(), save_log)
    decorated.apply(uuid4(), "start", {})

    assert events == ["executed", "logged"]