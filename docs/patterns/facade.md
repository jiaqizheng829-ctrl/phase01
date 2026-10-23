# Facade Pattern — Phase 7

## Purpose

The Dashboard needs location details, assigned devices, latest readings, and an automation recommendation.

Instead of making the frontend or router collect these separately, I use LocationOverviewFacade as one entry point.

```python
facade.get_overview(location_id)
```

## What the facade does

LocationOverviewFacade coordinates:

- OverviewRepository for the location, zones, assigned devices, and latest readings.
- AutomationRepository for the saved strategy key.
- AutomationService for the current recommendation.

The facade combines their results into LocationOverviewDto.

It does not contain SQL, translate sensor payloads, or implement irrigation algorithms. Database queries stay in repositories, sensor translation stays in adapters, and irrigation policies stay in strategies.

## Overview response

The endpoint is:

```text
GET /api/locations/{location_id}/overview
```

The response includes:

- `location`: ID and name.
- `device_counts`: assigned sensor and actuator counts.
- `zones`: every zone, its thresholds, assigned devices, and latest readings.
- `strategy_key`: the saved key or null.
- `last_recommendation`: action and reason, or null.

A device is included only when its location and zone assignment belong to the requested location.

Empty zones remain in the response. A device without a reading remains in `devices` but has no entry in `latest_readings`.

Readings include tracking status and sampling interval from the device table.

## Recommendation behavior

Despite its name, `last_recommendation` is calculated during each overview request.

When a strategy is saved, the facade calls the existing AutomationService.evaluate() method directly. It does not call the evaluate HTTP endpoint or copy the strategy algorithms.

When no strategy is saved, the endpoint returns HTTP 200 with both strategy fields set to null.

Recommendations are not saved in a new table, and overview does not send pump commands.

## Query design

The overview repository uses:

1. One query for the location and all its zones, using an outer join.
2. One query for assigned devices.
3. One query for the latest readings across those device IDs.

The reading query uses `row_number()` grouped by device ID. It orders readings by `recorded_at`, then by reading ID to resolve ties. Only the first row for each device is returned.

This avoids running a separate reading query for every device. If there are no assigned devices, the reading query is skipped.

Readings are not filtered by source. Manual reads, simulation sampling, and MQTT ingest all qualify.

The facade also reads the saved strategy key. When a key exists, the existing automation service performs its own queries, including per-zone moisture lookups. I keep those in the automation service so the facade does not duplicate decision logic.

## Database

No new table, SQL view, or migration was needed.

The existing tables are enough:

- `locations`
- `zones`
- `devices`
- `sensor_readings`
- `automation_rules`

The database revision remains `9d391b40fb2f` from Phase 6.

## API boundary and errors

The overview handler calls only the facade. Dependency construction is in `overview_dependencies.py`.

A missing location raises OverviewLocationNotFoundError, which the route maps to HTTP 404.

No saved strategy is a normal empty state, not an error.

Other failures are not converted into a misleading “location not found” response. Database and strategy failures remain distinguishable from missing locations.

The response model is documented in Scalar.

## Frontend

OverviewPanel is mounted in the Dashboard's `#overview` section.

The location dropdown uses the existing locations-list endpoint. The overview cards use one overview response rather than combining separate device, reading, and automation responses.

Selecting a location loads its overview. Refresh repeats the overview request.

The panel displays:

- Assigned sensor and actuator counts.
- Saved strategy and recommendation.
- Zone names and moisture thresholds.
- Device names, roles, and types.
- Reading values, units, timestamps, tracking, and sampling intervals.
- Empty states for missing strategies, readings, and devices.

The panel does not poll automatically. New readings or saved strategy changes appear on the next overview load or Refresh.

## Code locations

Paths are relative to the repository root.

- `backend/app/application/overview/dto.py`
- `backend/app/application/overview/facade.py`
- `backend/app/infrastructure/overview_repository.py`
- `backend/app/infrastructure/overview_dependencies.py`
- `backend/app/interfaces/api/overview.py`
- `frontend/src/api/overview.ts`
- `frontend/src/components/overview/OverviewPanel.tsx`
- `backend/tests/test_overview_api.py`

## Verification

The overview integration tests check:

- Unknown location returns 404.
- Location details match the seeded data.
- No saved strategy returns 200 with null strategy fields.
- Counts include assigned devices only.
- Unassigned devices and their readings are excluded.
- Empty zones remain visible.
- Devices without readings remain listed.
- The newest reading is selected, including an MQTT reading.
- Tracking and sampling settings come from the device.
- Recommendations match the existing evaluate service.
- New readings and changed strategies appear on the next overview request.

Results:

- Overview API tests: 2 passed.
- Complete backend suite: 99 passed, 1 dependency deprecation warning.
- Frontend TypeScript check and production build passed.
- Manual UI checks covered populated and empty locations.
- Scalar displayed the overview response schema.

## Facade versus Adapter

Adapter changes an incompatible interface into one the application can use. My Phase 5 sensor adapters normalize external readings.

Facade gives a simpler entry point to several existing subsystems. My Phase 7 facade combines location, device, reading, and automation information without replacing those subsystems.