from uuid import uuid4

import pytest

from app.domain.actuators.ports import ActuatorPort
from app.domain.commands.base import Command
from app.domain.commands.invoker import (
    COMMAND_REGISTRY,
    CommandInvoker,
    UnknownCommandError,
)


class RecordingPort(ActuatorPort):
    def __init__(self):
        self.calls = []

    def apply(self, device_id, command, payload):
        self.calls.append((device_id, command, payload))


@pytest.mark.parametrize(
    "command_type,port_command,payload,target_state",
    [
        ("start_pump", "start", {}, "running"),
        ("stop_pump", "stop", {}, "idle"),
        (
            "set_light_level",
            "set_light_level",
            {"level": 0.5},
            "running",
        ),
    ],
)
def test_invoker_executes_registered_commands(
    command_type,
    port_command,
    payload,
    target_state,
):
    device_id = uuid4()
    port = RecordingPort()
    invoker = CommandInvoker()

    command = invoker.create(command_type, device_id, payload)
    invoker.execute(command, port)

    assert port.calls == [(device_id, port_command, payload)]
    assert command.command_type == command_type
    assert command.target_state == target_state


def test_unknown_command_is_rejected():
    invoker = CommandInvoker()

    with pytest.raises(UnknownCommandError):
        invoker.create("unknown_command", uuid4(), {})


def test_command_copies_payload_before_execution():
    device_id = uuid4()
    payload = {"level": 1, "metadata": {"source": "original"}}
    invoker = CommandInvoker()
    command = invoker.create("set_light_level", device_id, payload)

    payload["level"] = 0.5
    payload["metadata"]["source"] = "changed"

    port = RecordingPort()
    invoker.execute(command, port)

    assert port.calls == [
        (
            device_id,
            "set_light_level",
            {"level": 1, "metadata": {"source": "original"}},
        )
    ]


def test_registry_can_add_command_without_changing_invoker(monkeypatch):
    class CustomCommand(Command):
        command_type = "custom_action"
        target_state = "running"
        device_type = "water_pump"

        def execute(self, port):
            port.apply(self.device_id, "custom_action", self.payload)

    monkeypatch.setitem(COMMAND_REGISTRY, "custom_action", CustomCommand)

    device_id = uuid4()
    port = RecordingPort()
    invoker = CommandInvoker()

    command = invoker.create("custom_action", device_id, {"value": 2})
    invoker.execute(command, port)

    assert isinstance(command, CustomCommand)
    assert port.calls == [(device_id, "custom_action", {"value": 2})]