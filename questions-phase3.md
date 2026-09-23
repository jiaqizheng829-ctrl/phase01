\# Phase 3 — Abstract Factory questions



\## A. Pattern



1\. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently ( for each piece) instead of as a \*\*family\*\*?`if format`



\*\*Note\*\*



\*\*\*My Answer\*\*\*



Abstract Factory creates a matching family of related products through one shared interface. If each product is selected using separate conditionals, the application can accidentally combine incompatible products, such as simulation sensors and edge actuators. Selecting one family factory keeps their family keys and configuration defaults consistent.



2\. Name the main participants (\*\*abstract factory\*\*, \*\*concrete factory\*\*, \*\*abstract products\*\*, \*\*concrete products\*\*, \*\*client\*\*). How does choosing a factory at the start \*\*commit\*\* the client to one family?



\*\*Note\*\*



\*\*\*My Answer\*\*\*



The abstract factory is `DeviceFamilyFactory`. The concrete factories are `SimulationDeviceFactory` and `EdgeHardwareFactory`. Abstract products represent the shared sensor and actuator contracts; this lab represents both roles through the domain `Device`. Concrete products are the family-configured moisture sensors, light sensors, water pumps, and grow lights returned by each factory. They do not need separate subclasses in this implementation.



The client is `DeviceFamilyService`. It selects a factory using the family key and requests the complete kit through `create\_device\_set()`. That factory supplies every sibling in the kit, committing that provisioning operation to one family.



3\. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?



\*\*Note\*\*



\*\*\*My Answer\*\*\*



Use Abstract Factory when several related products must be selected together and the application supports alternative families with compatibility requirements. Simulation and edge device kits are an example. Skip it when only one product type needs to be created, mixing implementations is valid, or ordinary configuration is sufficient. Factory Method may be simpler for creating individual product variants.



\## B. This phase of the application



4\. In this lab, what is a \*\*device family\*\*, and what does (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?`create\_device\_set()`



\*\*Note\*\*



\*\*\*My Answer\*\*\*



A device family is a set of greenhouse devices intended for the same environment, with a shared family key and matching defaults. In our implementation, `create\_device\_set()` returns four domain `Device` objects: a moisture sensor, a light sensor, a water pump, and a grow light.



Simulation devices use the `simulation` protocol, while edge devices use `gpio\_stub`. Mixing incompatible siblings would produce a kit with inconsistent operating assumptions. The edge protocol is currently a configuration hint; it does not control real hardware in this phase.



5\. Phase 2 Factory Method creators still exist. How does Abstract Factory \*\*compose\*\* them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?



\*\*Note\*\*



\*\*\*My Answer\*\*\*



Our family factory calls `MoistureSensorCreator` and `LightSensorCreator` from Phase 2. It uses their results to construct domain devices with family-specific metadata and configuration, then adds matching actuators.



Deleting those creators would remove reusable sensor construction logic and the extension points used by Phase 2. Sensor defaults could become duplicated across family factories, making changes and testing harder. Factory Method remains responsible for individual sensor types, while Abstract Factory coordinates the whole family.



6\. Why add a column on the existing table (with a default/backfill such as ) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?`device\_familydevices"simulation"`



\*\*Note\*\*



\*\*\*My Answer\*\*\*



Adding `device\_family` to the existing `devices` table keeps the shared device structure in one place. The repository and unified devices API can then filter records by family and role without querying separate tables or duplicating schemas.



The migration uses a non-null column with a server default of `"simulation"`, which gives existing Phase 2 rows a valid family. Without a backfill or a default that fills existing rows, adding the non-null column can fail. If nulls are allowed instead, old sensors may be excluded from family-filtered results or fail application validation.



7\. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). can filter by and . Why must the UI be able to filter by family? Why do routes from Phase 2 still need to work?`GET /api/devicesfamilyrole/api/sensors`



\*\*Note\*\*



\*\*\*My Answer\*\*\*



The UI must filter by family so selecting Simulation or Edge shows the devices belonging to that environment. Our family switcher sends the selected `family` to `GET /api/devices` and reloads the list when the selection changes. The API also supports filtering by `role`.



The Phase 2 `/api/sensors` routes must continue working because existing clients and the Sensors dashboard still use them. Phase 3 adds unified device management while preserving earlier functionality.



\## C. Compare, contrast, and scenarios



8\. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which \*\*one\*\* product?” versus “which product \*\*line\*\*?” and mention that Abstract Factory often \*\*uses\*\* Factory Method–style methods inside.



\*\*Note\*\*



\*\*\*My Answer\*\*\*



Factory Method answers “which \*\*one\*\* product?” by delegating individual product creation to a concrete creator, such as a moisture sensor creator. Abstract Factory answers “which product \*\*line\*\*?” by selecting a coherent family of related products, such as a simulation or edge kit containing sensors and actuators. Abstract Factory often uses Factory Method–style methods inside. Our family factories reuse the Phase 2 sensor creators and combine their products with matching actuators.



9\. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?



\*\*Note\*\*



\*\*\*My Answer\*\*\*



Direct construction can reintroduce mixed-family kits or incorrect defaults, such as an edge sensor combined with a simulation actuator. It also spreads creation rules into HTTP code, where they can drift away from the factory’s rules.



Our HTTP handler passes the requested family to `DeviceFamilyService`. The service resolves the factory, creates the kit, and asks the repository to save it. The handler then uses `to\_device\_dto()` to convert the saved domain devices into response DTOs. DTOs describe transferred data rather than decide which devices to create.



10\. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?



\*\*Note\*\*



\*\*\*My Answer\*\*\*



Abstract Factory is for related products that must form a compatible family, not every object that an application creates. Locations, readings, and devices have different responsibilities and creation lifecycles. Putting all of them into one factory would increase coupling and make unrelated changes affect the same component.



Our family factory should create matching sensor and actuator kits. Locations and readings should use their own appropriate creation processes, with devices assigned to locations separately once the required objects exist.
