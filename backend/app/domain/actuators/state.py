from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


class IllegalTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class ActuatorState:
    name: str
    transitions: Mapping[str, str]

    def allowed_commands(self) -> list[str]:
        return list(self.transitions)

    def target_for(self, command: str) -> str:
        target = self.transitions.get(command)

        if target is None:
            raise IllegalTransitionError(
                f"Command '{command}' is not allowed in state '{self.name}'."
            )

        return target


def make_state(name: str, transitions: dict[str, str]) -> ActuatorState:
    return ActuatorState(
        name=name,
        transitions=MappingProxyType(transitions),
    )


STATES = MappingProxyType({
    "idle": make_state(
        "idle",
        {
            "start": "running",
            "turn_off": "off",
            "enter_maintenance": "maintenance",
            "report_error": "error",
        },
    ),
    "running": make_state(
        "running",
        {
            "stop": "idle",
            "report_error": "error",
        },
    ),
    "off": make_state(
        "off",
        {
            "turn_on": "idle",
            "enter_maintenance": "maintenance",
            "report_error": "error",
        },
    ),
    "error": make_state(
        "error",
        {
            "reset": "idle",
            "enter_maintenance": "maintenance",
        },
    ),
    "maintenance": make_state(
        "maintenance",
        {
            "finish_maintenance": "idle",
            "report_error": "error",
        },
    ),
})


def get_state(name: str) -> ActuatorState:
    state = STATES.get(name)

    if state is None:
        raise IllegalTransitionError(
            f"Unknown actuator state: '{name}'."
        )

    return state