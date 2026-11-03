from app.domain.actuators.state import (
    IllegalTransitionError,
    get_state,
)


class ActuatorContext:
    def __init__(self, state: str = "idle") -> None:
        self._state = get_state(state)

    @property
    def state(self) -> str:
        return self._state.name

    def allowed_commands(self) -> list[str]:
        return self._state.allowed_commands()

    def apply_command(self, command: str) -> None:
        target = self._state.target_for(command)
        self._state = get_state(target)

    def transition(self, target: str) -> None:
        get_state(target)

        for command, next_state in self._state.transitions.items():
            if next_state == target:
                self.apply_command(command)
                return

        raise IllegalTransitionError(
            f"Transition from '{self.state}' to '{target}' is not allowed."
        )