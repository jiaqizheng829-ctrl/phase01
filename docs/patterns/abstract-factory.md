\# Abstract Factory — Greenhouse Device Families



\## Problem



The greenhouse application needs matching sensors and actuators for different environments. Selecting every device independently could mix simulation devices with edge devices that use different configuration assumptions.



\## Solution



`DeviceFamilyFactory` defines `create\_device\_set()`. Its concrete factories, `SimulationDeviceFactory` and `EdgeHardwareFactory`, each create two sensors and two actuators: a moisture sensor, a light sensor, a water pump, and a grow light.



All devices in a kit share the same `device\_family`. Simulation devices use the `simulation` protocol, while edge devices use `gpio\_stub`. Edge configuration is a placeholder for later hardware integration; it does not access real GPIO.



The family factories reuse the Phase 2 `MoistureSensorCreator` and `LightSensorCreator`. They combine those sensors with matching actuators and family-specific defaults.



\## Factory Method vs Abstract Factory



Factory Method answers “which one product?” and creates an individual sensor type. Abstract Factory answers “which product line?” and creates a coherent family of sensors and actuators. In this application, Abstract Factory composes the existing Factory Method creators rather than replacing them.



\## Code Locations



\- `backend/app/domain/devices/entity.py`: shared domain `Device`.

\- `backend/app/domain/devices/family\_factory.py`: abstract factory, concrete families, and family lookup.

\- `backend/app/domain/sensors.py`: existing Phase 2 sensor creators.

\- `backend/app/application/devices/family\_service.py`: selects a factory, creates a kit, and requests persistence.

\- `backend/app/application/devices/dto.py`: API response model.

\- `backend/app/application/devices/mappers.py`: converts domain devices into DTOs.

\- `backend/app/infrastructure/device\_repository.py`: saves kits and filters devices.

\- `backend/app/interfaces/api/devices.py`: list and provision endpoints.

\- `frontend/src/components/devices/`: family switcher, device list, and provisioning controls.



\## Domain Device and DTO



The domain `Device` describes a greenhouse device without depending on FastAPI, SQLAlchemy, or Pydantic. `DeviceDto` defines the response structure used at the HTTP boundary.



A dedicated application mapper converts a persisted domain device into a DTO. The family factory and repository do not import DTOs.



\## Persistence and API



All devices use the existing `devices` table. The migration adds a non-null `device\_family` column with a `simulation` server default and an index. Existing sensor rows therefore remain valid.



The repository saves each kit in one transaction and rolls back if saving fails.



\- `GET /api/devices` supports optional `family` and `role` query parameters.

\- `POST /api/devices/provision?family=simulation` creates and saves a simulation kit.

\- `POST /api/devices/provision?family=edge` creates and saves an edge kit.

\- Successful provisioning returns HTTP 201 and four device DTOs.

\- An unknown provisioning family returns HTTP 400.

\- Phase 2 `/api/sensors` endpoints remain available.



Each successful provisioning request creates a new kit.



\## Dashboard



The Devices section lets users select Simulation or Edge, view family and role badges, and create a kit. Changing family reloads the filtered list. After provisioning, the device list and the existing Sensors section are refreshed.



\## Verification



The factory and Phase 2 creator tests passed: 9 tests. They check kit composition, family consistency, configuration differences, reuse of sensor creators, independent configurations, and rejection of unknown families.



Three API tests passed using the separate `greenhouse\_phase3\_test` database. They check provisioning, retrieval through subsequent requests, family and role filters, unknown-family rejection, and Phase 2 sensor compatibility. Each test rolls back its changes.



The frontend TypeScript check and production build also passed.



\## Extension Exercise



To add a third family, implement another `DeviceFamilyFactory`, supply coherent defaults, and register its family key. Add the family to the frontend type and selector, and extend the tests. The provisioning service and existing database structure can remain unchanged.
