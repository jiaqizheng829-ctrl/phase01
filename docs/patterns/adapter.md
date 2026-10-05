# Phase 5 — Adapter

## Problem

Different sensor drivers can return different field names and units. For example, the vendor stub returns `measurement: 41` with the unit `percent`, while this application uses `value: 0.41` and `unit: vwc`.

If the application handled every driver's format directly, adding a new driver would require changes throughout the reading flow.

## Ports and normalized readings

`SensorPort` defines `read(device)`. Simulation and vendor adapters implement this interface and return the same `Reading` type.

A reading contains:

- `device_id`
- `value`
- `unit`
- `source`
- `recorded_at`, including its timezone

Moisture uses `vwc` on a 0–1 scale. Light uses `lux`.

The domain ports and reading type do not import FastAPI, SQLAlchemy or Pydantic.

## Adapters

The sensor adapters are in `backend/app/infrastructure/adapters/sensors/`.

- `simulation.py` generates moisture between 0.2 and 0.6 vwc, or light between 200 and 2000 lux.
- `vendor_stub.py` wraps a stub driver and translates its field names and units. Its readings use `source="vendor"`.
- `mqtt.py` translates a dictionary such as `{"value": 0.41, "unit": "vwc"}` into a reading with `source="mqtt"`.

The MQTT adapter exposes `translate(device, payload)`. It does not open a broker connection or provide a device HTTP endpoint. Those transports belong to Phase 12.

Adapters translate data and validate its format. They do not decide when to water a zone.

## Adapter selection

`selector.py` uses the device's `default_config`:

- `protocol: simulation` selects the simulation adapter.
- `protocol: simulation` with `driver: vendor_stub` selects the vendor stub.
- `protocol: mqtt` requires an incoming payload. A manual read returns an explanatory error instead of generating fake device data.

New simulation kits use `simulation`; new edge kits use `mqtt`. Changing the factory does not rewrite previously saved device configurations.

## One reading write path

`ReadingIngest` is in `backend/app/application/readings/service.py`.

For a manual read, it loads the device, selects an adapter and calls `read()`. It then passes the result through `record()`.

`record()` checks that the reading belongs to the requested sensor and has an appropriate unit and value. It calls `ReadingRepository.insert()` and maps the saved reading to `ReadingDto`.

The simulation sampler and translated MQTT readings also use `record()`. This keeps the persistence path shared.

Each successful read adds a row to `sensor_readings`. Old readings are retained. The table has a device foreign key and an index on device ID and descending reading time.

## Sampling settings and automatic sampling

`devices` stores `sampling_interval_seconds` and `tracking_enabled`. These columns are the source of truth.

The migration copies numeric intervals from the old JSON configuration. Missing or non-numeric values use 300 seconds. Values below 5 are raised to 5; fractional values are rounded up.

`SimulationSampler.run_once(now)` checks enabled sensors with `protocol: simulation`. It records a reading when there is no previous reading or the device's interval has elapsed.

Disabled devices, MQTT devices and actuators are skipped. A manual read is still allowed when tracking is off, and its timestamp also affects when the next automatic sample is due.

The application lifespan starts the sampling loop. It checks every second and uses a separate database session for each round. This implementation is intended to run with one backend worker.

Setting `SIMULATION_SAMPLER_ENABLED=false` disables the loop. It is also disabled when `TEST_DATABASE_URL` is set, so API tests do not start background sampling against the normal database.

## Simulation actuator

`ActuatorPort` defines `apply(device_id, command, payload)`.

`SimulationActuatorAdapter` records commands in memory and copies their payloads. It does not control physical hardware. Phase 9 can wrap this port with decorators.

## API and frontend

The reading and sampling endpoints are:

- `POST /api/sensors/{id}/read`
- `GET /api/sensors/{id}/readings?limit=20`
- `PATCH /api/devices/{id}/sampling`

Missing devices return 404. Adapter errors and sampling intervals below 5 seconds return 400. FastAPI handles malformed request types separately.

Sensor cards show the latest stored value, source and timestamp. Users can read immediately, change the interval and save the tracking setting.

Cards temporarily poll the latest-reading endpoint every five seconds. Phase 12 will replace this polling with WebSocket updates. Reloading the page fetches saved readings and settings from the backend.

## Tests

Tests cover:

- Simulation value ranges and units.
- Vendor field and percentage conversion.
- MQTT translation without network access.
- Invalid MQTT payloads.
- Simulation actuator command recording.
- Sampling intervals, tracking changes and skipped device types.
- API reads appending database rows and returning ordered history.
- Saved sampling settings and rejected invalid intervals.
- MQTT readings saved through the shared ingest service.
- Factory protocols for simulation and edge kits.

Sampler tests pass explicit timestamps instead of sleeping. API tests use a separate database and roll back their data.

## Adding another vendor

Add a new adapter implementing `SensorPort`, wrap the vendor client, and translate its result into `Reading`. Extend the selector with a documented driver option and add translation tests.

The ingest service, readings table and frontend reading format can stay the same.