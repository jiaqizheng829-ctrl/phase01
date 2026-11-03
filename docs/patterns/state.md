# Phase 8: State

## Purpose

I used the State pattern to manage actuator lifecycle states. Each actuator has one current state, and that state decides which commands are allowed.

This keeps transition rules in the backend domain instead of repeating them in API handlers and React components.

## Implementation

- `ActuatorContext` holds the current state.
- `ActuatorState` provides allowed commands and their target states.
- Five state objects define the lifecycle rules.
- `ActuatorStateService` loads the saved state, applies a transition, and saves the result.
- `ActuatorStateRepository` handles database access.

I used immutable state objects with transition maps instead of a separate class for every state. The context delegates command validation to its current state object.

## States and transitions

| Current state | Command | Next state |
| --- | --- | --- |
| idle | start | running |
| idle | turn_off | off |
| idle | enter_maintenance | maintenance |
| idle | report_error | error |
| running | stop | idle |
| running | report_error | error |
| off | turn_on | idle |
| off | enter_maintenance | maintenance |
| off | report_error | error |
| error | reset | idle |
| error | enter_maintenance | maintenance |
| maintenance | finish_maintenance | idle |
| maintenance | report_error | error |

Transitions not listed here are rejected. For example, a running actuator cannot move directly to maintenance. It must stop first.

## Persistence

The `actuator_states` table stores:

- `device_id`: primary key and foreign key to the device.
- `state`: current lifecycle state.
- `updated_at`: time of the latest update.

The migration creates idle states for existing actuators. New actuators receive an idle state in the same transaction as device creation. Sensors do not receive actuator state rows.

The database also restricts state values to the five supported names.

## Transition flow

1. The API receives a target state.
2. The service locks and reads the actuator and its state.
3. The service creates an `ActuatorContext`.
4. The context checks whether the transition is legal.
5. The repository saves the new state.
6. The service commits and returns the state and allowed commands.

If validation fails, the transaction is rolled back. The saved state remains unchanged.

State objects do not perform SQL queries, commit transactions, or return HTTP responses.

## API

- `GET /api/devices/{device_id}/state` returns the current state and allowed commands.
- `POST /api/devices/{device_id}/transition` requests a transition using a target state.
- Device list responses also include `state` and `allowed_commands`.

An illegal transition returns HTTP 409. A missing device or a sensor passed to the actuator state API returns HTTP 404.

For sensors, device responses contain `state: null` and an empty command list.

## Frontend

Actuator cards show a state badge and the allowed commands returned by the API. The frontend does not calculate the transition rules.

When the water pump changes from idle to running, refreshing the device list changes its displayed commands to `stop` and `report_error`.

The command labels are informational. They are not command buttons.

## Scope

The transition endpoint changes the saved lifecycle state only. It does not send commands to a physical pump or light.

Phase 10 can use the allowed commands when adding command execution. The backend must still validate each command against the current state.

## State and Strategy

Phase 6 uses Strategy to choose an irrigation recommendation policy for a location.

Phase 8 uses State to control which operations are legal for an actuator during its lifecycle.

A strategy is selected as a policy. An actuator state changes through legal transitions.

## Verification

- 55 domain tests passed.
- 10 actuator state API tests passed.
- The full backend suite passed: 164 tests.
- TypeScript checking and the frontend build passed.
- A running-to-maintenance request returned HTTP 409 and preserved the stored state.
- The running state survived a backend restart.
- Device cards displayed the updated state and allowed commands after refresh.
- The GET state endpoint schema was checked in Scalar.

The backend tests reported one dependency deprecation warning.