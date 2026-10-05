# Greenhouse Dashboard — Phase 5: Adapter

A smart greenhouse coursework project using React, FastAPI, and PostgreSQL.

## Phase 5 submission

- [Phase 5 questions and answers](phases/phase-05/questions.md)
- [Adapter implementation notes](docs/patterns/adapter.md)
- [Phase 5 requirements](phases/phase-05/requirements.md)

Answers use the provided question template and its original Your Answer fields.

## Phase 5 features

- Read simulation sensors through `SensorPort`.
- Translate vendor stub data into normalized readings.
- Translate MQTT payload dictionaries without connecting to a broker.
- Save readings in PostgreSQL and query recent history.
- Automatically sample enabled simulation sensors.
- Change the sampling interval and tracking setting.
- Show saved readings, sources and timestamps on sensor cards.
- Provide a simulation actuator implementing `ActuatorPort`.

Moisture readings use `vwc` on a 0–1 scale. Light readings use `lux`.

The simulation adapter generates moisture between 0.2 and 0.6 vwc and light between 200 and 2000 lux.

## Start the application

Requirements:

- Docker Desktop installed with its engine running.
- Ports 5173, 8000 and 5432 available.

Run these commands from the project root:

```powershell
docker compose -f compose.yml up -d --build
docker compose -f compose.yml ps
```

The backend applies migrations before starting the API.

Check the database revision:

```powershell
docker compose -f compose.yml exec backend alembic current
```

The Phase 5 revision is `3b45041792c3`.

Open:

- [Dashboard](http://localhost:5173/dashboard)
- [Health check](http://localhost:8000/health)
- [Scalar API documentation](http://localhost:8000/scalar)
- [OpenAPI JSON](http://localhost:8000/openapi.json)

## Using sensor cards

1. Open the Sensors section.
2. Click Read now to take and save a reading.
3. Enter a sampling interval of at least 5 seconds.
4. Choose whether tracking is enabled.
5. Click Save settings.

Disabling tracking stops automatic sampling. Manual reads remain available for simulation sensors.

Cards fetch the latest saved reading every five seconds. This is temporary polling until Phase 12 adds WebSocket updates. Refreshing the page reloads readings and sampling settings from the backend.

## Adapter selection

Device configuration selects the adapter:

| Configuration | Behavior |
| --- | --- |
| `protocol: simulation` | Generate a simulated reading |
| `protocol: simulation`, `driver: vendor_stub` | Translate vendor stub data |
| `protocol: mqtt` | Translate an incoming payload; no manual generation |

New edge kits use `mqtt`. This phase does not provide a broker connection or device HTTP ingestion endpoint. MQTT translation and persistence are tested directly.

Previously saved device configurations are not rewritten when the factory changes.

## Persistence and automatic sampling

Readings are appended to `sensor_readings`, with a device foreign key and an index on device ID and descending reading time.

`ReadingIngest.record()` is the shared application write path for manual reads, sampling and translated MQTT readings.

Sampling settings live in columns on `devices`. The migration backfills numeric intervals from old JSON configuration. Missing or non-numeric settings use 300 seconds; values below 5 are raised to 5 and fractions are rounded up.

The sampler checks every second. It records only enabled sensors whose protocol is `simulation` and whose interval has elapsed. Device zone assignment does not control sampling.

Run this implementation with one backend worker. `SIMULATION_SAMPLER_ENABLED=false` disables the background loop when set in the backend environment. The loop is also disabled when `TEST_DATABASE_URL` is set.

## Reading and sampling API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/sensors` | List sensors and saved sampling settings |
| POST | `/api/sensors` | Create a simulation sensor |
| POST | `/api/sensors/{id}/read` | Read and persist a measurement |
| GET | `/api/sensors/{id}/readings?limit=20` | Get history, newest first |
| PATCH | `/api/devices/{id}/sampling` | Save interval and tracking settings |

History limits range from 1 to 100.

Example sampling body:

```json
{
  "sampling_interval_seconds": 30,
  "tracking_enabled": true
}
```

Missing devices return 404. Adapter errors and out-of-range intervals return 400. Malformed request types use FastAPI's validation responses.

## Retained configuration features

Phase 4 features remain available:

- Create a location with one or more zones using Builder.
- List and reopen saved configurations.
- Add, edit and delete zones.
- Keep at least one zone per location.
- Assign devices to zones across saved locations.
- Clear assignments without deleting devices.
- Delete locations while retaining their devices.

Zone moisture thresholds use values between 0 and 1, with the low threshold strictly below the high threshold.

Device assignment updates `zone_id` and `location_id` together. Deleting a zone or location clears affected assignments.

## Using the configuration UI

1. Open Configuration and click New location.
2. Enter a location name.
3. Add zones to the draft.
4. Click Create location.
5. Select a saved location to manage its zones.

Device cards offer an Assigned zone selector. Choose Unassigned to clear an assignment.

Location deletion requires confirmation. The last zone cannot be deleted individually. Schedules are JSON objects; an empty schedule is `{}`.

## Configuration API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/locations/config` | Create a location and zones |
| GET | `/api/locations` | List locations |
| GET | `/api/locations/{location_id}/config` | Read a configuration |
| DELETE | `/api/locations/{location_id}` | Delete a location |
| POST | `/api/locations/{location_id}/zones` | Add a zone |
| PATCH | `/api/locations/{location_id}/zones/{zone_id}` | Edit a zone |
| DELETE | `/api/locations/{location_id}/zones/{zone_id}` | Delete a zone |
| PATCH | `/api/devices/{id}/zone` | Assign or unassign a device |
| GET | `/api/locations/{location_id}/zones/{zone_id}/devices` | List assigned devices |

## Backend tests

API tests require a separate database named `greenhouse_phase3_test`. The name is retained from earlier phases.

Create it once if it does not already exist:

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

API tests roll back their changes. Without `TEST_DATABASE_URL`, database API tests are skipped.

Adapter and sampler unit tests use no broker or database. Sampler tests pass explicit timestamps instead of sleeping.

## Frontend check

```powershell
docker compose -f compose.yml exec frontend npm run build
```

This runs TypeScript checking and the Vite production build.

## Verification performed

- The 67-test backend suite passed.
- The subsequently added factory protocol test passed separately.
- Frontend TypeScript checking and production build passed.
- The Phase 5 migration was applied to the application and test databases.
- Database inspection confirmed the reading foreign key, index and sampling constraint.
- Manual checks covered saved history, interval changes, automatic sampling, tracking off and manual reading while tracking was off.
- Dashboard checks covered reading display, saved sampling settings and the tracking controls.

## Troubleshooting

Inspect logs:

```powershell
docker compose -f compose.yml logs backend db frontend
```

If the frontend shows an old page after saving:

```powershell
docker compose -f compose.yml restart frontend
```

Then refresh the browser.

If Docker cannot connect to its engine, start Docker Desktop and wait until it is running.

## Stop the application

```powershell
docker compose -f compose.yml down
```

This stops the services and retains the database volume.

## Earlier phases

- [Phase 4 questions and answers](phases/phase-04/questions.md)
- [Builder notes](docs/patterns/builder.md)
- [Phase 3 questions and answers](phases/phase-03/questions.md)
- [Abstract Factory notes](docs/patterns/abstract-factory.md)
- [Phase 1 answers](questions.md)

## References and assistance

The teacher-provided example solutions are reference projects, separate from this implementation:

- [Phase 3 example](https://github.com/xamk-mire/DesignPatterns-Example-Project/tree/phase-3)
- [Phase 4 example](https://github.com/xamk-mire/DesignPatterns-Example-Project/tree/phase-4)

The Phase 1 foundation was compared with the course example, and some corrections were adapted from it.

AI assistance was used for implementation guidance, debugging, test examples and documentation drafts in Phases 4 and 5.