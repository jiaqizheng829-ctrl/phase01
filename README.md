# Greenhouse Dashboard — Phase 4: Builder

A smart greenhouse coursework project using React, FastAPI, and PostgreSQL.

## Phase 4 submission

- [Phase 4 questions and answers](phases/phase-04/questions.md)
- [Builder implementation notes](docs/patterns/builder.md)

Phase 4 answers use the provided questions.md template and its original Your Answer fields.

## Features

- Create a location with one or more zones using Builder.
- List saved locations and open their configurations.
- Delete locations while keeping their devices.
- Add and edit zones, including names, moisture thresholds, and schedules.
- Delete zones while keeping at least one zone per location.
- Assign existing devices to zones or clear their assignments.
- View the devices assigned to each zone.
- Manage configurations through the dashboard.
- Select device zones from all saved locations, grouped by location.

Moisture thresholds use values between 0 and 1. The low value must be strictly less than the high value.

Device assignment updates zone_id and location_id together. Deleting a zone or location clears the affected assignments without deleting devices.

## Requirements

- Docker Desktop installed and its engine running.
- Ports 5173, 8000, and 5432 available.

Run the commands below from the project root.

## Start the application

This project contains both compose.yml and docker-compose.yml. The commands below explicitly use compose.yml.

```powershell
docker compose -f compose.yml up -d --build
docker compose -f compose.yml ps
```

The backend startup command applies migrations automatically before starting the API.

Check the database revision:

```powershell
docker compose -f compose.yml exec backend alembic current
```

The Phase 4 revision is `16f6a0abd449 (head)`.

## Open the application

- [Dashboard](http://localhost:5173/dashboard)
- [Health check](http://localhost:8000/health)
- [Scalar API documentation](http://localhost:8000/scalar)
- [OpenAPI JSON](http://localhost:8000/openapi.json)

The health check should return:

```json
{"status":"ok","db":"ok"}
```

## Using the configuration UI

1. Open Configuration and click New location.
2. Enter a location name.
3. Add one or more zones to the draft list.
4. Click Create location.
5. Select a saved location to manage its zones.

The location list reloads from the API after a page refresh. Creating a new location keeps existing locations.

Device cards have an Assigned zone selector. Options show `Location name — Zone name`. Select Unassigned to clear an assignment.

Deleting a location requires confirmation. The last zone in a location cannot be deleted.

Schedule values are entered as JSON objects. An empty schedule is `{}`.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/locations/config` | Create a location and zones |
| GET | `/api/locations` | List locations, newest first |
| GET | `/api/locations/{location_id}/config` | Read a configuration |
| DELETE | `/api/locations/{location_id}` | Delete a location |
| POST | `/api/locations/{location_id}/zones` | Add a zone |
| PATCH | `/api/locations/{location_id}/zones/{zone_id}` | Edit a zone |
| DELETE | `/api/locations/{location_id}/zones/{zone_id}` | Delete a zone |
| PATCH | `/api/devices/{id}/zone` | Assign or unassign a device |
| GET | `/api/locations/{location_id}/zones/{zone_id}/devices` | List devices in a zone |

The Builder is used for new configurations. Saved-zone management and device assignment use separate operations.

## Run backend tests

API tests require a separate database named `greenhouse_phase3_test`. The name is retained for compatibility with the existing Phase 3 tests.

Create it once if it does not already exist:

```powershell
docker compose -f compose.yml exec db createdb -U greenhouse greenhouse_phase3_test
```

Apply migrations to the test database:

```powershell
docker compose -f compose.yml exec -e DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend alembic upgrade head
```

Run all backend tests:

```powershell
docker compose -f compose.yml exec -e TEST_DATABASE_URL=postgresql+psycopg2://greenhouse:greenhouse@db:5432/greenhouse_phase3_test backend python -m pytest -q
```

API tests roll back their changes after each test. Without TEST_DATABASE_URL, the API tests are skipped.

## Frontend checks

```powershell
docker compose -f compose.yml exec frontend npm run build
```

The build script runs TypeScript checking and the Vite production build.

## Verification

During development:

- All 35 backend tests passed before the final DTO configuration cleanup.
- The frontend TypeScript check and production build passed.
- Migrations were applied successfully to a newly created empty test database.
- Manual checks covered location creation, listing and deletion; zone creation, editing and deletion; invalid thresholds; last-zone protection; device assignment and cancellation; and assignment cleanup after deletion.
- Dashboard checks covered configuration display, creating a location, device assignment, cross-location selection, and location deletion with device retention.

## Environment configuration

Docker Compose provides the database connection settings. A separate .env file is not required for this Docker setup.

The root .env.example contains example settings for running the backend directly on the host.

The sample credentials are for local coursework.

## Troubleshooting

Inspect service logs:

```powershell
docker compose -f compose.yml logs backend db frontend
```

If the frontend still shows an old page after saving, restart its development service and refresh the browser:

```powershell
docker compose -f compose.yml restart frontend
```

If Docker cannot connect to its engine, check that Docker Desktop is running.

## Stop the application

```powershell
docker compose -f compose.yml down
```

This stops the services and keeps the database volume.

## Earlier phases

- [Phase 3 questions and answers](phases/phase-03/questions.md)
- [Abstract Factory implementation notes](docs/patterns/abstract-factory.md)
- [Phase 1 answers](questions.md)

## Reference and assistance

The Phase 1 foundation was compared with the course example, and parts of its corrections were adapted from that example:

[Course example project](https://github.com/xamk-mire/DesignPatterns-Example-Project/tree/main/Example-project)

AI assistance was used for Phase 4 implementation guidance, debugging, test examples, and documentation drafts.