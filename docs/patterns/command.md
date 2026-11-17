# Command Pattern — Phase 10

## Intent

The Command pattern represents an actuator action as an object.
Each command stores the target device and payload and exposes
execute(port).

This separates the HTTP request from the actuator implementation and
allows command attempts to be recorded in PostgreSQL.

## Commands and invoker

The implementation provides:

- StartPumpCommand: calls the port with start; targets running.
- StopPumpCommand: calls the port with stop; targets idle.
- SetLightLevelCommand: calls the port with set_light_level;
  targets running.

COMMAND_REGISTRY maps command type strings to command classes.
CommandInvoker creates the registered class and invokes execute(port).
It does not use command-type branches.

A new command can be registered without changing the invoker.
Its state permissions and any required UI controls must also be defined.

## Execution flow

1. The router passes the request to CommandService.
2. The service validates the actuator and locks its saved state.
3. The invoker creates the command from the registry.
4. ActuatorContext checks the command against allowed_commands().
5. A disallowed command is recorded as rejected without calling the port
   or changing the state.
6. An allowed command executes through the Phase 9 decorated port.
7. After successful execution, the service calls
   ActuatorContext.transition only when the target state differs.
8. The service saves the command result and commits the transaction.

Changing the level of an already running light does not write its state
again or reset its state timestamp.

## Integration with Decorator

build_actuator_port constructs this stack:

LoggingDecorator → MaxRunTimeDecorator → SimulationActuatorAdapter

Logging wraps the runtime guard so that blocked execution attempts are
also recorded.

When the runtime limit is exceeded:

- The inner adapter is not called.
- The command status is failed.
- The error message is Max run time exceeded.
- The actuator state and timestamp stay unchanged.
- The execution log records the failure with maxRunTime and logging.

The command service supplies a logging callback that adds the execution
log to the current session without committing early. Command logs,
execution logs, and successful state changes are committed together.
Database errors cause a rollback.

## HTTP API

POST /api/commands accepts:

{
  "command_type": "start_pump",
  "device_id": "<actuator UUID>",
  "payload": {}
}

Responses:

- 200: success or failed, with the command log row.
- 409: rejected, with the same command log row shape.
- 400: unknown command type; no command log is written.
- 404: missing device or non-actuator device.

GET /api/commands?limit=50 returns the newest records first.
The limit must be between 1 and 200.

Each history row includes id, command_type, device_id, payload, status,
error_message, and created_at.

Scalar exposes the request and response documentation at /scalar.

## Frontend

CommandPanel is rendered in #controls.

Buttons are disabled when their command names are absent from the
device's allowed_commands.

The light level defaults to 1 and can be edited.
After each attempt, the panel reloads actuator states and command history.

Device DTOs expose Phase 10 command names such as start_pump.
The existing Phase 8 state endpoints retain their lifecycle command names.

## Why not call the port from the router?

Calling the port directly would bypass the command objects and invoker.
It would also make it easier to omit state guards or command history.

The router handles HTTP details. The application service coordinates
execution and persistence. Commands describe individual actions, while
the decorated port handles execution policies.

## Validation

Automated tests cover:

- Forwarding all three commands through the invoker.
- Rejecting unknown command types.
- Copying payloads when commands are created.
- Extending the registry without changing the invoker.
- Successful start and stop with persisted state and logs.
- Illegal-state rejection without state changes or execution logs.
- Runtime failure with both failure logs and unchanged state.
- Updating a running light without rewriting its state.
- Missing devices and sensors returning 404.
- History ordering, limits, and invalid limits.

## Limitations and next phase

Actuation is currently simulated.
Commands execute synchronously; this phase does not implement a queue,
undo, or automatic retries.

Phase 11 can introduce observer notifications for command outcomes.