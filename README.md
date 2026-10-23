# Greenhouse Dashboard — Phase 7: Facade

A greenhouse coursework project using React, FastAPI, and PostgreSQL.

## Phase 7 submission

- [Phase 7 questions and answers](phases/phase-07/questions.md)
- [Facade pattern notes](docs/patterns/facade.md)
- [Phase 7 requirements](phases/phase-07/requirements.md)

## Phase 7 features

- One overview API for a selected location.
- Assigned sensor and actuator counts.
- All zones, including zones without devices.
- Assigned devices and their latest saved readings.
- Tracking status and sampling interval on reading summaries.
- Saved strategy and a recommendation calculated on each request.
- Dashboard Overview panel with a location selector and Refresh button.

No new database table, view, or migration was needed.

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

The current revision remains `9d391b40fb2f` from Phase 6.

Open:

- [Dashboard](http://localhost:5173/dashboard)
- [Overview](http://localhost:5173/dashboard#overview)
- [Automation](http://localhost:5173/dashboard#automation)
- [Health check](http://localhost:8000/health)
- [Scalar API documentation](http://localhost:8000/scalar)
- [OpenAPI JSON](http://localhost:8000/openapi.json)

## Using Overview

1. Open the Dashboard and scroll to Overview.
2. Select a location.
3. View device counts, strategy, recommendation, and zone cards.
4. Click Refresh to load current data.

The location selector uses the existing locations-list endpoint. Overview cards come from one overview response. Refresh repeats that overview request.

The panel does not poll automatically.

### Overview rules

- Only devices assigned to a zone in the selected location are included.
- Unassigned devices are excluded from counts and zone cards.
- Every zone is included, even if it has no devices.
- Devices without readings remain listed with a “No reading available” message.
- Each device with readings has only its newest reading included.
- Reading source is not filtered: manual, sampled, and MQTT-ingested readings qualify.
- Tracking and sampling settings come from the device table.

A location without a saved strategy still loads normally. Its strategy and recommendation fields are null.

The recommendation is calculated during each request using the existing automation service. It is not stored in a new table, and no pump commands are sent.

## Overview API

```text
GET /api/locations/{location_id}/overview
```

Main response fields:

| Field | Contents |
| --- | --- |
| `location` | Location ID and name |
| `device_counts` | Assigned sensor and actuator counts |
| `zones` | All zones, thresholds, devices, and latest readings |
| `strategy_key` | Saved strategy key or null |
| `last_recommendation` | Calculated action and reason, or null |

Missing locations return HTTP 404.

The route calls only LocationOverviewFacade. Dependency construction is handled separately.

The facade coordinates repositories and AutomationService. It does not contain SQL, sensor translation, or irrigation algorithms.

The overview repository loads assigned devices together and uses one window-function query for their latest readings. It does not run a reading query for each device. The existing automation service still performs its own per-zone moisture lookups.

## Automation from Phase 6

Each location can save a conservative or aggressive strategy.

- Conservative recommends irrigation below the zone's lower moisture threshold.
- Aggressive recommends irrigation below the midpoint of its lower and upper thresholds.
- Equality with the policy threshold returns `wait`.

For moisture 0.4 with thresholds 0.2 and 0.8:

| Strategy | Recommendation |
| --- | --- |
| Conservative | wait |
| Aggressive | irrigate |

Each zone uses its own assigned moisture sensors. Missing sensors or readings produce `wait` with a reason.

The overall recommendation is `irrigate` if at least one zone recommends irrigation.

### Using Automation

1. Select a location in Automation.
2. Select a strategy.
3. Click Save strategy.
4. Click Evaluate.

Save changed selections before evaluating. Saved settings are stored in `automation_rules`, with one rule per location.

Evaluation uses the latest stored reading without an age limit. Automatic sampling can change readings between evaluations.

### Automation API

| Method | Path |
| --- | --- |
| GET | `/api/locations/{location_id}/automation` |
| PUT | `/api/locations/{location_id}/automation` |
| POST | `/api/locations/{location_id}/automation/evaluate` |

Save body:

```json
{
  "strategy_key": "conservative"
}
```

Missing locations return 404. Unknown strategies and evaluation without a saved strategy return 400.

## Sensors and sampling from Phase 5

- Simulation sensors generate readings through SensorPort.
- Vendor adapters translate stub data.
- MQTT adapters translate payloads without connecting to a broker.
- Readings are saved in `sensor_readings`.
- ReadingIngest.record() is the shared write path.
- Enabled simulation sensors are sampled automatically.

Moisture uses `vwc` on a 0–1 scale. Light uses `lux`.

Simulation values range from 0.2 to 0.6 for moisture and 200 to 2000 for light.

### Sensor cards

1. Click Read now to save a reading.
2. Set an interval of at least 5 seconds.
3. Choose whether tracking is enabled.
4. Click Save settings.

Turning tracking off stops automatic sampling. Manual reads remain available for simulation sensors.

Sensor cards fetch the latest saved reading every five seconds.

### Adapter selection

| Configuration | Behavior |
| --- | --- |
| `protocol: simulation` | Generate simulated readings |
| `protocol: simulation`, `driver: vendor_stub` | Translate vendor stub data |
| `protocol: mqtt` | Translate incoming payloads; no manual generation |

New edge kits use MQTT configuration. No broker connection or device HTTP ingestion endpoint is provided.

Previously saved configurations are not rewritten when factory defaults change.

Run one backend worker. The sampler can be disabled with `SIMULATION_SAMPLER_ENABLED=false` in the backend environment. It is also disabled when `TEST_DATABASE_URL` is set.

### Sensor API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/sensors` | List sensors |
| POST | `/api/sensors` | Create simulation sensor |
| POST | `/api/sensors/{id}/read` | Save a manual reading |
| GET | `/api/sensors/{id}/readings?limit=20` | Get reading history |
| PATCH | `/api/devices/{id}/sampling` | Save sampling settings |

History limits range from 1 to 100.

## Location configuration

Earlier configuration features remain available:

- Create locations and zones using Builder.
- Edit zone thresholds and schedules.
- Assign or unassign devices.
- Delete zones while keeping at least one per location.
- Delete locations while retaining devices.

Thresholds must satisfy `0 <= low < high <= 1`.

Device assignment updates both `location_id` and `zone_id`. Deleting a zone or location clears affected assignments.

Use Configuration to create and edit locations. Use the device cards' zone selectors to assign devices.

### Configuration API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/locations/config` | Create location and zones |
| GET | `/api/locations` | List locations |
| GET | `/api/locations/{location_id}/config` | Read configuration |
| DELETE | `/api/locations/{location_id}` | Delete location |
| POST | `/api/locations/{location_id}/zones` | Add zone |
| PATCH | `/api/locations/{location_id}/zones/{zone_id}` | Edit zone |
| DELETE | `/api/locations/{location_id}/zones/{zone_id}` | Delete zone |
| PATCH | `/api/devices/{id}/zone` | Assign or unassign device |
| GET | `/api/locations/{location_id}/zones/{zone_id}/devices` | List assigned devices |

## Backend tests

API tests use a separate database named `greenhouse_phase3_test`. This name is retained from earlier phases.

Create it once if it does not exist:

```powershell
docker compose -f compose.yml exec db createdb -U greenhouse greenhouse_phase3_test
```

Apply existing migrations:

```powershell
docker compose -f compose.yml exec -e DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend alembic upgrade head
```

Run all tests:

```powershell
docker compose -f compose.yml exec -e TEST_DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend python -m pytest -q
```

Run Overview tests only:

```powershell
docker compose -f compose.yml exec -e TEST_DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend python -m pytest tests/test_overview_api.py -q
```

API tests roll back temporary data. Without TEST_DATABASE_URL, database API tests are skipped.

## Frontend check

```powershell
docker compose -f compose.yml exec frontend npm run build
```

This runs TypeScript checking and the production build.

## Verification performed

- Complete backend suite: **99 passed, 1 warning**.
- Overview API tests: **2 passed**.
- Frontend TypeScript checking and production build passed.
- Manual Overview checks covered populated and empty locations.
- Scalar displayed the overview response schema.

Overview tests verified:

- Missing location returns 404.
- No saved strategy returns 200 with null strategy fields.
- Counts exclude unassigned devices.
- Empty zones remain included.
- Devices without readings remain listed.
- Latest readings include device sampling settings.
- MQTT readings are eligible.
- Recommendations match the existing evaluation service.
- New readings and changed strategies appear on the next GET.

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

If Overview shows old readings or settings, click its Refresh button.

If Overview shows no devices, check that devices are assigned to zones in the selected location.

If no strategy is saved, use Automation to save one, then refresh Overview.

If Docker cannot connect to its engine, start Docker Desktop and wait until it is running.

## Stop the application

```powershell
docker compose -f compose.yml down
```

This stops services and retains the database volume.

## Earlier phases

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

AI assistance was used for implementation guidance, debugging, test examples, and documentation drafts in Phases 4–7.