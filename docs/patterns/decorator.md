# Phase 9: Decorator

## Purpose

I used Decorator to add logging and a maximum runtime check
around the actuator adapter. Each wrapper keeps the same
ActuatorPort interface, so I did not need a separate adapter
class for every combination of policies.

## Main classes

- ActuatorPort defines apply(device_id, command, payload).
- SimulationActuatorAdapter records simulated commands.
- MaxRunTimeDecorator checks the saved actuator state and time.
- LoggingDecorator records successful and failed attempts.
- ActuatorExecutionRepository saves and reads execution logs.
- ActuatorExecutionService builds the decorator chain.

## Composition

The chain is created in ActuatorExecutionService:

LoggingDecorator
  -> MaxRunTimeDecorator
    -> SimulationActuatorAdapter

Logging is the outer wrapper. This allows it to record a failed
attempt even when the runtime check blocks the inner adapter.

The API router does not build the chain.

## Runtime policy

The runtime check reads state and updated_at from actuator_states,
which was added in Phase 8.

If the state is running and the elapsed time is at least
30 minutes, the decorator raises MaxRunTimeExceededError with
the message "Max run time exceeded".

The inner adapter is not called in this case. Other states are
not blocked by this runtime policy.

The clock can be supplied by tests, so the 30-minute boundary
can be checked without waiting.

This check happens when apply is called. It is not a background
timer and does not automatically stop a device.

## Execution logs

Logs are stored in actuator_execution_log with these fields:

- id
- device_id
- success
- policy_applied
- message
- created_at

A successful attempt stores:

- success: true
- policy_applied: ["logging"]
- message: null

A runtime-blocked attempt stores:

- success: false
- policy_applied: ["maxRunTime", "logging"]
- message: "Max run time exceeded"

LoggingDecorator saves the failed record before re-raising the
error. The repository commits the log so it remains available
after the error and in later requests.

Missing devices and sensors are rejected before entering the
decorator chain. They do not create actuator execution logs.

## API and dashboard

GET /api/actuators/executions?limit=20 returns the newest logs
first. The limit must be between 1 and 100.

The dashboard Execution log panel shows the device ID, time,
result, policies and message. Its Refresh button reloads records
from the database. An empty list shows "No execution attempts yet."

## Scope

Execution uses the simulation adapter. It does not send commands
to real hardware or change the Phase 8 lifecycle state.

This phase does not check command names against allowed_commands.
An unknown non-empty command can pass through the simulation
adapter if the runtime policy allows it.

## Verification

I checked successful and blocked attempts manually. Both records
were visible through the API and on the dashboard. The temporary
running state used in the timeout check was restored afterwards.

The decorator tests cover the runtime boundary, blocked inner
calls, logging order, unknown commands and adapter failures.

The database and API tests cover saved success and failure logs,
sorting, limits, empty results and invalid devices.

Results:

- Decorator tests: 13 passed.
- Execution database and API tests: 10 passed.
- Full backend suite: 187 passed, 1 warning.
- Frontend TypeScript check and production build passed.

The warning is a TestClient dependency deprecation warning.