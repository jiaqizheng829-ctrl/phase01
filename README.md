# Greenhouse Dashboard — Phase 9: Decorator

## Phase 9 submission

- [Phase 9 questions and answers](phases/phase-09/questions.md)
- [Decorator pattern notes](docs/patterns/decorator.md)
- [Phase 9 requirements](phases/phase-09/requirements.md)
- [Phase 9 guided check](phases/phase-09/guided-check.md)

## Phase 9 features

I added two decorators around the simulation actuator adapter:

LoggingDecorator -> MaxRunTimeDecorator -> SimulationActuatorAdapter

ActuatorExecutionService builds this chain.

- Logging saves successful and failed attempts in PostgreSQL.
- MaxRunTime checks the saved Phase 8 state and updated_at.
- Requests are blocked when the actuator has been running for at least 30 minutes.
- Blocked requests do not reach the simulation adapter.
- The dashboard shows the latest 20 execution records.

This phase uses simulation only. Applying a command does not change
the lifecycle state or control real hardware. Command names are not
checked against allowed_commands in this phase.

The runtime check runs when apply is called. It does not automatically
stop a device after 30 minutes.

## Phase 9 database

The migration is `9258538de3ba`, following Phase 8 revision
`16dd3ce021ac`.

It adds actuator_execution_log with:

- id
- device_id
- success
- policy_applied
- message
- created_at

Upgrade and check:

```powershell
docker compose -f compose.yml exec backend alembic upgrade head
docker compose -f compose.yml exec backend alembic current
```

## Execution log API and UI

GET /api/actuators/executions?limit=20 returns records newest first.
The limit must be between 1 and 100.

Open [Execution log](http://localhost:5173/dashboard#executions)
and click Refresh to load current records.

A successful attempt shows:

- Success
- Policies: logging
- Message: —

A runtime-blocked attempt shows:

- Failed
- Policies: maxRunTime, logging
- Message: Max run time exceeded

The panel also shows the device ID and local time.
With no records, it shows "No execution attempts yet."

Execution is currently triggered through ActuatorExecutionService
in scripts and tests. The dashboard displays logs; it does not
provide an execution button.

## Phase 9 verification

I manually checked that a successful simulated execution saves a log.

I also temporarily set a simulated actuator to running with an
updated_at timestamp 30 minutes earlier. The request was blocked,
the inner adapter was not called, and the failure log was saved.
The original state and timestamp were restored after the check.

Both records appeared through the API and on the dashboard.

Test results:

- Decorator tests: 13 passed.
- Execution database and API tests: 10 passed.
- Full backend suite: 187 passed, 1 warning.
- Container frontend TypeScript check and production build passed.

The warning concerns a deprecated TestClient dependency.
The editor's separate frontend diagnostics have not yet been resolved.

Run the full backend suite against the test database:

```powershell
docker compose -f compose.yml exec -e DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend alembic upgrade head

docker compose -f compose.yml exec -e TEST_DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend python -m pytest -q
```

Build the frontend:

```powershell
docker compose -f compose.yml exec frontend npm run build
```

## Previous implementation and operating instructions

The following sections describe the existing Phase 8 functionality
and shared application setup. Phase 8 revision and test results are
historical; the current Phase 9 results are listed above.


A greenhouse coursework project using React, FastAPI, and PostgreSQL.

## Phase 8 submission

- [Phase 8 questions and answers](phases/phase-08/questions.md)
- [State pattern notes](docs/patterns/state.md)
- [Phase 8 requirements](phases/phase-08/requirements.md)
- [Phase 8 guided check](phases/phase-08/guided-check.md)

## Phase 8 features

- Five actuator states: idle, running, off, error, and maintenance.
- Transition rules in the backend domain.
- Saved actuator states in PostgreSQL.
- Idle states for existing and newly created actuators.
- State and allowed commands in device responses.
- State badges and allowed-command labels on device cards.
- A demo API for changing lifecycle state.
- Tests for legal transitions, rejected transitions, and persistence.

The demo transition API changes the saved lifecycle state only. It does not send commands to physical devices.

## Start the application

Requirements:

- Docker Desktop with its engine running.
- Ports 5173, 8000, and 5432 available.

Run from the project root:

```powershell
docker compose -f compose.yml up -d --build
docker compose -f compose.yml ps
```

The backend applies migrations before starting.

Check the database revision:

```powershell
docker compose -f compose.yml exec backend alembic current
```

The Phase 8 revision is `16dd3ce021ac`.

Open:

- [Dashboard](http://localhost:5173/dashboard)
- [Overview](http://localhost:5173/dashboard#overview)
- [Automation](http://localhost:5173/dashboard#automation)
- [Health check](http://localhost:8000/health)
- [Scalar API documentation](http://localhost:8000/scalar)
- [OpenAPI JSON](http://localhost:8000/openapi.json)

## Using actuator states

1. Open the Dashboard.
2. Find the Devices section.
3. Select a device family.
4. View the state badge and allowed commands on actuator cards.
5. Click Refresh after changing a state through the API.

Sensors do not display actuator state badges.

The allowed commands are informational labels, not clickable command buttons.

For an idle actuator, the allowed commands are:

- start
- turn_off
- enter_maintenance
- report_error

For a running actuator, only `stop` and `report_error` are allowed.

## State transitions

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

Other transitions are rejected, including transitions to the same state.

For example, a running actuator must stop before entering maintenance.

## State design and persistence

`ActuatorContext` holds the current state and delegates command checks to an `ActuatorState` object.

The five state objects use immutable transition maps. State rules do not contain HTTP handling or database commits.

`ActuatorStateService` loads the saved state, checks the transition, and saves the result through `ActuatorStateRepository`.

The `actuator_states` table contains:

- `device_id`: primary key and foreign key to the device.
- `state`: current lifecycle state.
- `updated_at`: latest update time.

The migration creates idle state rows for existing actuators. New actuators and their initial states are saved in the same transaction. Sensors do not receive state rows.

Transition requests lock the actuator and state rows before checking the current state. Illegal transitions roll back without changing the saved state.

State survives a backend restart.

## Actuator state API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/devices/{device_id}/state` | Read state and allowed commands |
| POST | `/api/devices/{device_id}/transition` | Request a lifecycle transition |

Example transition body:

```json
{
  "target": "running"
}
```

This target is legal when the actuator is idle.

Example response:

```json
{
  "device_id": "cb92c162-932e-46cb-ac4b-4bd67a5a3eb5",
  "state": "running",
  "allowed_commands": [
    "stop",
    "report_error"
  ]
}
```

Use an actuator ID from your own device list when testing.

- Illegal transitions return HTTP 409.
- Missing devices and sensors passed to these endpoints return HTTP 404.
- Invalid request bodies return HTTP 422.

Device list and zone-assignment responses also include `state` and `allowed_commands`. Sensors return null state and an empty command list.

Phase 10 can use these rules when adding command execution. The backend must still check the current state before executing a command.

## Overview from Phase 7

The Overview panel shows:

- Assigned sensor and actuator counts.
- All zones, including empty zones.
- Assigned devices and their latest saved readings.
- Tracking status and sampling intervals.
- Saved strategy and a calculated recommendation.

Select a location and click Refresh to load current data. The panel does not poll automatically.

```text
GET /api/locations/{location_id}/overview
```

Main response fields are `location`, `device_counts`, `zones`, `strategy_key`, and `last_recommendation`.

Unassigned devices are excluded. Devices without readings remain listed. A location without a saved strategy returns null strategy and recommendation fields.

The facade combines repositories and the existing automation service. Recommendations are calculated during the request, and no pump commands are sent.

## Automation from Phase 6

Each location can save a conservative or aggressive strategy.

- Conservative recommends irrigation below the lower moisture threshold.
- Aggressive recommends irrigation below the midpoint of the lower and upper thresholds.
- Equality with the policy threshold returns `wait`.
- Missing moisture sensors or readings return `wait` with a reason.

In Automation, select a location and strategy, click Save strategy, then Evaluate.

| Method | Path |
| --- | --- |
| GET | `/api/locations/{location_id}/automation` |
| PUT | `/api/locations/{location_id}/automation` |
| POST | `/api/locations/{location_id}/automation/evaluate` |

Evaluation uses the latest saved readings. It does not control actuator lifecycle or send physical commands.

## Sensors and sampling from Phase 5

- Simulation sensors generate readings.
- Vendor adapters translate stub data.
- MQTT adapters translate payloads without connecting to a broker.
- Readings are saved in `sensor_readings`.
- Enabled simulation sensors are sampled automatically.

Moisture uses `vwc` on a 0–1 scale. Light uses `lux`.

On sensor cards:

1. Click Read now to save a simulated reading.
2. Set a sampling interval of at least 5 seconds.
3. Choose whether tracking is enabled.
4. Click Save settings.

Turning tracking off stops automatic sampling. Manual reads remain available for simulation sensors.

Sensor cards fetch the latest saved reading every five seconds.

| Method | Path |
| --- | --- |
| GET | `/api/sensors` |
| POST | `/api/sensors` |
| POST | `/api/sensors/{id}/read` |
| GET | `/api/sensors/{id}/readings?limit=20` |
| PATCH | `/api/devices/{id}/sampling` |

History limits range from 1 to 100.

Run one backend worker. Automatic sampling is disabled when `TEST_DATABASE_URL` is set. It can also be disabled with `SIMULATION_SAMPLER_ENABLED=false`.

## Devices and location configuration

Earlier features remain available:

- Create simulation or edge device kits.
- Create locations and zones.
- Edit zone thresholds and schedules.
- Assign or unassign devices.
- Delete zones while keeping at least one per location.
- Delete locations while retaining devices.

Moisture thresholds must satisfy `0 <= low < high <= 1`.

Device assignment updates both `location_id` and `zone_id`. Deleting a zone or location clears affected assignments.

Use Configuration to manage locations and zones. Use the device cards' zone selectors to assign devices.

## Backend tests

API tests use a separate database named `greenhouse_phase3_test`. The name is retained from earlier phases.

Create it once if it does not exist:

```powershell
docker compose -f compose.yml exec db createdb -U greenhouse greenhouse_phase3_test
```

Apply migrations to the test database:

```powershell
docker compose -f compose.yml exec -e DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend alembic upgrade head
```

Run all tests:

```powershell
docker compose -f compose.yml exec -e TEST_DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend python -m pytest -q
```

Run state domain tests:

```powershell
docker compose -f compose.yml exec backend python -m pytest tests/test_actuator_states.py -q
```

Run actuator state API tests:

```powershell
docker compose -f compose.yml exec -e TEST_DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend python -m pytest tests/test_actuator_states_api.py -q
```

API tests roll back temporary data. Database API tests are skipped when `TEST_DATABASE_URL` is missing.

## Frontend check

```powershell
docker compose -f compose.yml exec frontend npm run build
```

This runs TypeScript checking and the production build.

## Verification performed

- Full backend suite: **164 passed, 1 warning**.
- State domain tests: **55 passed**.
- Actuator state API tests: **10 passed**.
- Frontend TypeScript checking and production build passed.
- Existing actuators had saved idle states.
- Illegal transitions returned HTTP 409 and preserved the database state.
- The running state survived a backend restart.
- Device cards showed running with only `stop` and `report_error`.
- The pump was restored to idle after the manual checks.
- Scalar displayed the GET state response fields.

The warning is a Starlette TestClient dependency deprecation warning. It did not fail the tests.

## Troubleshooting

Inspect logs:

```powershell
docker compose -f compose.yml logs backend db frontend
```

If the frontend shows an old page:

```powershell
docker compose -f compose.yml restart frontend
```

Then refresh the browser.

Click the Devices Refresh button after changing an actuator state through the API.

If a transition returns 409, read the current state and allowed commands. Choose a legal transition.

If Overview shows old data, click its Refresh button. If devices are missing, check their zone assignments.

If Docker cannot connect to its engine, start Docker Desktop and wait until it is running.

## Stop the application

```powershell
docker compose -f compose.yml down
```

This stops services and retains the database volume.

## Earlier phases

- [Phase 7 questions](phases/phase-07/questions.md)
- [Facade notes](docs/patterns/facade.md)
- [Phase 6 questions](phases/phase-06/questions.md)
- [Strategy notes](docs/patterns/strategy.md)
- [Phase 5 questions](phases/phase-05/questions.md)
- [Adapter notes](docs/patterns/adapter.md)
- [Phase 4 questions](phases/phase-04/questions.md)
- [Builder notes](docs/patterns/builder.md)
- [Phase 3 questions](phases/phase-03/questions.md)
- [Abstract Factory notes](docs/patterns/abstract-factory.md)
- [Phase 1 answers](questions.md)

## References and assistance

The teacher's example projects were used as references. They are separate from this implementation:

- [Phase 3 example](https://github.com/xamk-mire/DesignPatterns-Example-Project/tree/phase-3)
- [Phase 4 example](https://github.com/xamk-mire/DesignPatterns-Example-Project/tree/phase-4)

The Phase 1 foundation was compared with the course example, and some corrections were adapted from it.

AI assistance was used for implementation guidance, debugging, test examples, and documentation drafts in Phases 4–9.