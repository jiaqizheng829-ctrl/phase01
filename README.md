# Greenhouse Dashboard — Phase 6: Strategy

A greenhouse coursework project using React, FastAPI, and PostgreSQL.

## Phase 6 submission

- [Phase 6 questions and answers](phases/phase-06/questions.md)
- [Strategy pattern notes](docs/patterns/strategy.md)
- [Phase 6 requirements](phases/phase-06/requirements.md)

## Phase 6 features

- Save a conservative or aggressive strategy for each location.
- Evaluate each zone using its own thresholds and latest saved moisture reading.
- Show recommendations and reasons in the Dashboard.
- Return `wait` when a zone has no moisture sensor or no saved reading.
- Keep decision logic separate from API handling and database access.

Strategies only recommend actions. They do not start pumps.

## Start the application

Requirements:

- Docker Desktop with its engine running.
- Ports 5173, 8000, and 5432 available.

Run from the project root:

```powershell
docker compose -f compose.yml up -d --build
docker compose -f compose.yml ps
```

The backend applies database migrations before starting.

Check the current revision:

```powershell
docker compose -f compose.yml exec backend alembic current
```

The Phase 6 revision is `9d391b40fb2f`, following Phase 5 revision `3b45041792c3`.

Open:

- [Dashboard](http://localhost:5173/dashboard)
- [Automation panel](http://localhost:5173/dashboard#automation)
- [Health check](http://localhost:8000/health)
- [Scalar API documentation](http://localhost:8000/scalar)
- [OpenAPI JSON](http://localhost:8000/openapi.json)

## Using automation

1. Create a location and zones in Configuration if needed.
2. Assign a moisture sensor to a zone using the device card.
3. Use Read now or allow automatic sampling to save a reading.
4. Open Automation and select the location.
5. Select Conservative or Aggressive.
6. Click Save strategy.
7. Click Evaluate.

The panel shows the saved strategy and each zone's recommendation. Refreshing the page loads saved settings again for the selected location.

Save a changed selection before evaluating. A location without a saved strategy cannot be evaluated.

## Strategy behavior

Conservative recommends irrigation below the zone's lower threshold.

Aggressive recommends irrigation below the midpoint of the zone's lower and upper thresholds.

| Low | High | Moisture | Conservative | Aggressive |
| --- | --- | --- | --- | --- |
| 0.2 | 0.8 | 0.4 | wait | irrigate |

At exactly the policy's threshold, the result is `wait`.

Each zone uses the latest reading among its assigned moisture sensors. Readings from light sensors, unassigned sensors, and other zones are excluded.

A missing sensor or missing reading produces `wait` with a reason. A location without zones produces `wait` with an empty zone list.

The overall action is `irrigate` if any zone recommends irrigation. Individual zone results explain where it is recommended.

Automatic sampling may change moisture between evaluations. The unit and API tests use fixed readings to compare policies reliably.

## Strategy persistence and architecture

The `automation_rules` table stores one strategy per location:

- UUID primary key
- Unique `location_id` foreign key
- `strategy_key`
- JSONB `parameters`, currently unused
- `updated_at`

Saving again updates the existing row. Deleting a location also deletes its rule.

The domain contains plain Python strategies and context objects. The application service loads the saved key and calls the selected strategy for each zone. Infrastructure repositories handle database queries, and the API returns DTOs.

Evaluation uses existing database readings without adding a scheduler or MQTT connection. The latest reading has no age limit in this implementation.

Recommendations are displayed in the UI but are not stored as recommendation history.

## Automation API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/locations/{location_id}/automation` | Read saved strategy |
| PUT | `/api/locations/{location_id}/automation` | Save or change strategy |
| POST | `/api/locations/{location_id}/automation/evaluate` | Evaluate using the saved strategy |

Save body:

```json
{
  "strategy_key": "conservative"
}
```

Known keys are `conservative` and `aggressive`.

- Missing location: HTTP 404.
- Unknown strategy: HTTP 400.
- Evaluation before saving a strategy: HTTP 400.
- Malformed request bodies use FastAPI validation responses.

Evaluation returns the location ID, saved strategy key, overall action and reason, and a `zones` list with individual results.

## Retained sensor features

Phase 5 features remain available:

- Simulation sensor readings through `SensorPort`.
- Vendor stub data translation.
- MQTT payload translation without a broker connection.
- Persisted reading history.
- Automatic sampling for enabled simulation sensors.
- Sampling interval and tracking controls.
- Sensor cards showing readings, sources, and timestamps.
- A simulation actuator implementing `ActuatorPort`.

Moisture uses `vwc` on a 0–1 scale. Light uses `lux`.

The simulation adapter generates moisture between 0.2 and 0.6 and light between 200 and 2000 lux.

### Sensor cards

1. Click Read now to save a reading.
2. Set a sampling interval of at least 5 seconds.
3. Choose whether tracking is enabled.
4. Click Save settings.

Turning tracking off stops automatic sampling. Manual reads remain available for simulation sensors.

Cards fetch the latest reading every five seconds. This is temporary polling until the later WebSocket phase.

### Adapter selection

| Configuration | Behavior |
| --- | --- |
| `protocol: simulation` | Generate simulated readings |
| `protocol: simulation`, `driver: vendor_stub` | Translate vendor stub data |
| `protocol: mqtt` | Translate incoming payloads; no manual generation |

New edge kits use `mqtt`. There is no broker connection or device HTTP ingestion endpoint in this implementation. MQTT translation and persistence are tested directly.

Previously saved device configurations are not automatically rewritten when factory defaults change.

### Sampling and storage

Readings are appended to `sensor_readings`. `ReadingIngest.record()` is the shared write path for manual reads, sampling, and translated MQTT readings.

Sampling settings are stored on `devices`. The sampler checks every second and records enabled simulation sensors when their interval has elapsed.

Run one backend worker. Setting `SIMULATION_SAMPLER_ENABLED=false` in the backend environment disables the background loop. The loop is also disabled when `TEST_DATABASE_URL` is set.

### Reading API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/sensors` | List sensors and sampling settings |
| POST | `/api/sensors` | Create a simulation sensor |
| POST | `/api/sensors/{id}/read` | Take and save a reading |
| GET | `/api/sensors/{id}/readings?limit=20` | Read history, newest first |
| PATCH | `/api/devices/{id}/sampling` | Save sampling settings |

History limits range from 1 to 100.

Example sampling body:

```json
{
  "sampling_interval_seconds": 30,
  "tracking_enabled": true
}
```

## Retained configuration features

- Create locations with zones using Builder.
- Read and edit saved configurations.
- Add, edit, and delete zones.
- Keep at least one zone per location.
- Assign or unassign devices.
- Delete locations while retaining devices.

Moisture thresholds must satisfy `0 <= low < high <= 1`.

Device assignment updates `zone_id` and `location_id` together. Deleting a zone or location clears affected assignments.

### Configuration UI

1. Open Configuration and click New location.
2. Enter a name and add zones.
3. Click Create location.
4. Select a saved location to manage its zones.
5. Use device cards to assign sensors to zones.

Location deletion requires confirmation. Schedules are JSON objects; an empty schedule is `{}`.

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

API tests use a separate database named `greenhouse_phase3_test`. The name is retained from earlier phases.

Create it once if it does not exist:

```powershell
docker compose -f compose.yml exec db createdb -U greenhouse greenhouse_phase3_test
```

Apply migrations:

```powershell
docker compose -f compose.yml exec -e DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend alembic upgrade head
```

Run all backend tests:

```powershell
docker compose -f compose.yml exec -e TEST_DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend python -m pytest -q
```

Run only strategy unit tests:

```powershell
docker compose -f compose.yml exec backend python -m pytest tests/test_automation_strategies.py -q
```

Run only automation API tests:

```powershell
docker compose -f compose.yml exec -e TEST_DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend python -m pytest tests/test_automation_api.py -q
```

API tests roll back temporary data. Without `TEST_DATABASE_URL`, database API tests are skipped.

Strategy unit tests need no database or broker.

## Frontend check

```powershell
docker compose -f compose.yml exec frontend npm run build
```

This runs TypeScript checking and the Vite production build.

## Verification performed

- Complete backend suite: **97 passed, 1 warning**.
- Strategy unit tests: **23 passed**.
- Automation API tests: **6 passed**.
- Frontend TypeScript checking and production build passed.
- Phase 6 migration applied to application and test databases.
- API checks demonstrated different recommendations for the same stored moisture after switching strategies.
- Dashboard checks demonstrated loading saved strategies and displaying per-zone recommendations.
- Integration tests verified persistence, unknown keys, missing locations, unconfigured locations, empty locations, and zone reading isolation.

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

If Evaluate is disabled, save the selected strategy first.

A `wait` recommendation can be correct even for Aggressive. Check the displayed moisture, thresholds, and reason.

If Docker cannot connect to its engine, start Docker Desktop and wait until it is running.

## Stop the application

```powershell
docker compose -f compose.yml down
```

This stops services and retains the database volume.

## Earlier phases

- [Phase 5 questions and answers](phases/phase-05/questions.md)
- [Adapter notes](docs/patterns/adapter.md)
- [Phase 4 questions and answers](phases/phase-04/questions.md)
- [Builder notes](docs/patterns/builder.md)
- [Phase 3 questions and answers](phases/phase-03/questions.md)
- [Abstract Factory notes](docs/patterns/abstract-factory.md)
- [Phase 1 answers](questions.md)

## References and assistance

The teacher's example projects were used as references. They are separate from this implementation:

- [Phase 3 example](https://github.com/xamk-mire/DesignPatterns-Example-Project/tree/phase-3)
- [Phase 4 example](https://github.com/xamk-mire/DesignPatterns-Example-Project/tree/phase-4)

The Phase 1 foundation was compared with the course example, and some corrections were adapted from it.

AI assistance was used for implementation guidance, debugging, test examples, and documentation drafts in Phases 4, 5, and 6.