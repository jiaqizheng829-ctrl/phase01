from app.domain.actuators.state import (
    IllegalTransitionError,
    get_state,
)


COMMAND_TARGETS: dict[str, dict[str, dict[str, str]]] = {
    "water_pump": {
        "idle": {"start_pump": "running"},
        "running": {"stop_pump": "idle"},
    },
    "grow_light": {
        "idle": {"set_light_level": "running"},
        "running": {"set_light_level": "running"},
    },
}


class ActuatorContext:
    def __init__(
        self,
        state: str = "idle",
        *,
        device_type: str | None = None,
    ) -> None:
        self._state = get_state(state)
        self.device_type = device_type

    @property
    def state(self) -> str:
        return self._state.name

    def _command_targets(self) -> dict[str, str]:
        return COMMAND_TARGETS.get(
            self.device_type or "", {}
        ).get(self.state, {})

    def allowed_commands(self) -> list[str]:
        if self.device_type is None:
            return self._state.allowed_commands()

        return list(self._command_targets())

    def target_for(self, command: str) -> str:
        if self.device_type is None:
            return self._state.target_for(command)

        target = self._command_targets().get(command)
        if target is None:
            raise IllegalTransitionError(
                f"Command '{command}' is not allowed for "
                f"'{self.device_type}' in state '{self.state}'."
            )
        return target

    def apply_command(self, command: str) -> None:
        target = self.target_for(command)
        if target != self.state:
            self.transition(target)

    def transition(self, target: str) -> None:
        get_state(target)

        for next_state in self._state.transitions.values():
            if next_state == target:
                self._state = get_state(target)
                return

        raise IllegalTransitionError(
            f"Transition from '{self.state}' to '{target}' is not allowed."
        )