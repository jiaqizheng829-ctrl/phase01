import pytest

from app.domain.actuators.context import ActuatorContext
from app.domain.actuators.state import IllegalTransitionError


LEGAL_TRANSITIONS = [
    ("idle", "start", "running"),
    ("idle", "turn_off", "off"),
    ("idle", "enter_maintenance", "maintenance"),
    ("idle", "report_error", "error"),
    ("running", "stop", "idle"),
    ("running", "report_error", "error"),
    ("off", "turn_on", "idle"),
    ("off", "enter_maintenance", "maintenance"),
    ("off", "report_error", "error"),
    ("error", "reset", "idle"),
    ("error", "enter_maintenance", "maintenance"),
    ("maintenance", "finish_maintenance", "idle"),
    ("maintenance", "report_error", "error"),
]

EXPECTED_COMMANDS = {
    "idle": {
        "start",
        "turn_off",
        "enter_maintenance",
        "report_error",
    },
    "running": {"stop", "report_error"},
    "off": {"turn_on", "enter_maintenance", "report_error"},
    "error": {"reset", "enter_maintenance"},
    "maintenance": {"finish_maintenance", "report_error"},
}

STATE_NAMES = tuple(EXPECTED_COMMANDS)

LEGAL_PAIRS = {
    (source, target)
    for source, _, target in LEGAL_TRANSITIONS
}

ILLEGAL_PAIRS = [
    (source, target)
    for source in STATE_NAMES
    for target in STATE_NAMES
    if (source, target) not in LEGAL_PAIRS
]


def test_default_state_is_idle():
    actuator = ActuatorContext()

    assert actuator.state == "idle"


@pytest.mark.parametrize(
    "source, command, target",
    LEGAL_TRANSITIONS,
)
def test_legal_command_changes_state(source, command, target):
    actuator = ActuatorContext(source)

    actuator.apply_command(command)

    assert actuator.state == target
    assert set(actuator.allowed_commands()) == EXPECTED_COMMANDS[target]


@pytest.mark.parametrize(
    "source, command, target",
    LEGAL_TRANSITIONS,
)
def test_legal_target_transition(source, command, target):
    actuator = ActuatorContext(source)

    actuator.transition(target)

    assert actuator.state == target


@pytest.mark.parametrize("source, target", ILLEGAL_PAIRS)
def test_illegal_target_preserves_state(source, target):
    actuator = ActuatorContext(source)
    commands_before = actuator.allowed_commands()

    with pytest.raises(IllegalTransitionError):
        actuator.transition(target)

    assert actuator.state == source
    assert actuator.allowed_commands() == commands_before


@pytest.mark.parametrize("state", STATE_NAMES)
def test_allowed_commands_match_state(state):
    actuator = ActuatorContext(state)

    assert set(actuator.allowed_commands()) == EXPECTED_COMMANDS[state]


@pytest.mark.parametrize(
    "state, command",
    [
        ("running", "enter_maintenance"),
        ("running", "start"),
        ("off", "start"),
        ("error", "start"),
        ("maintenance", "start"),
        ("idle", "stop"),
        ("idle", "unknown_command"),
    ],
)
def test_illegal_command_preserves_state(state, command):
    actuator = ActuatorContext(state)

    with pytest.raises(IllegalTransitionError):
        actuator.apply_command(command)

    assert actuator.state == state


def test_unknown_initial_state_is_rejected():
    with pytest.raises(IllegalTransitionError):
        ActuatorContext("unknown")


def test_unknown_target_preserves_state():
    actuator = ActuatorContext("idle")

    with pytest.raises(IllegalTransitionError):
        actuator.transition("unknown")

    assert actuator.state == "idle"


def test_returned_commands_cannot_change_allowed_commands():
    actuator = ActuatorContext("running")

    commands = actuator.allowed_commands()
    commands.append("enter_maintenance")

    assert set(actuator.allowed_commands()) == {"stop", "report_error"}

    with pytest.raises(IllegalTransitionError):
        actuator.apply_command("enter_maintenance")

    assert actuator.state == "running"


def test_actuators_have_independent_states():
    pump = ActuatorContext()
    light = ActuatorContext()

    pump.apply_command("start")

    assert pump.state == "running"
    assert light.state == "idle"