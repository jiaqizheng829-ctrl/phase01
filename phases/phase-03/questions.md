# Phase 3 — Abstract Factory questions

**Pattern / focus:** Abstract Factory.

**Read first:** [Guide 03](../../materials/guides/03-abstract-factory.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example warrior/mage class kits) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to device families, provision, and the unified devices API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently (`if format` for each piece) instead of as a **family**?

> [!NOTE]
> ***Your Answer***
>
> Abstract Factory creates a matching family of related products through a shared interface. Choosing each product independently can mix incompatible siblings, such as simulation sensors with edge actuators. Selecting one family factory keeps the family keys and configuration defaults consistent.

2. Name the main participants (**abstract factory**, **concrete factory**, **abstract products**, **concrete products**, **client**). How does choosing a factory at the start **commit** the client to one family?

> [!NOTE]
> ***Your Answer***
>
> The abstract factory is DeviceFamilyFactory, and the concrete factories are SimulationDeviceFactory and EdgeHardwareFactory. Abstract products represent the shared sensor and actuator contracts; our lab represents both roles using the domain Device. Concrete products are the family-configured moisture sensor, light sensor, water pump, and grow light instances. The client is DeviceFamilyService. Once it selects a factory, it requests the entire kit from that factory, so the provisioning operation uses one family. Separate product subclasses are not required in our implementation.

3. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?

> [!NOTE]
> ***Your Answer***
>
> Use Abstract Factory when related products must work together and several alternative families exist, such as simulation and edge kits. Skip it when only one product type needs to be selected, mixing implementations is valid, or simple configuration is sufficient. Factory Method may be enough for individual product creation.

## B. This phase of the application

4. In this lab, what is a **device family**, and what does `create_device_set()` (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?

> [!NOTE]
> ***Your Answer***
>
> A device family is a coherent set of greenhouse devices sharing an environment, a family key, and compatible defaults. Our create_device_set() returns a list of four domain Device objects: a moisture sensor, a light sensor, a water pump, and a grow light. Simulation devices use the simulation protocol, while edge devices use gpio_stub. Mixing incompatible siblings would create inconsistent operating assumptions. The edge protocol is a configuration hint, not real hardware control in this phase.

5. Phase 2 Factory Method creators still exist. How does Abstract Factory **compose** them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?

> [!NOTE]
> ***Your Answer***
>
> The family factory calls the existing MoistureSensorCreator and LightSensorCreator from Phase 2, retains their sensor defaults, and adds family metadata and configuration. It combines those sensors with matching actuators. Deleting the creators would remove reusable construction logic and extension points, and could duplicate sensor rules across family factories. Factory Method handles individual sensor types; Abstract Factory coordinates the kit.

6. Why add a `device_family` column on the existing `devices` table (with a default/backfill such as `"simulation"`) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?

> [!NOTE]
> ***Your Answer***
>
> Adding device_family to the existing devices table preserves one shared device structure and lets the repository and unified API filter by family and role. Separate tables would duplicate schemas and complicate queries. Our migration adds a non-null column with a simulation server default that also fills existing rows. Without a backfill or an effective migration default, adding the non-null column could fail. If nulls remain allowed, old sensors could be missing from family-filtered results or fail validation.

7. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). `GET /api/devices` can filter by `family` and `role`. Why must the UI be able to filter by family? Why do `/api/sensors` routes from Phase 2 still need to work?

> [!NOTE]
> ***Your Answer***
>
> The UI needs family filtering so selecting Simulation or Edge displays devices from the selected environment rather than mixing both families. Our switcher sends the family query parameter and reloads the device list when the selection changes. The API also supports role filtering. Phase 2 /api/sensors routes must keep working because existing clients and the Sensors dashboard still depend on them.

## C. Compare, contrast, and scenarios

8. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which **one** product?” versus “which product **line**?” and mention that Abstract Factory often **uses** Factory Method–style methods inside.

> [!NOTE]
> ***Your Answer***
>
> Factory Method answers “which one product?” by delegating individual product creation to a concrete creator, such as a moisture sensor creator. Abstract Factory answers “which product line?” by selecting a coherent family of related products, such as a simulation or edge kit containing sensors and actuators. Abstract Factory often uses Factory Method-style methods inside: our family factories reuse the Phase 2 sensor creators and combine their results with matching actuators.

9. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?

> [!NOTE]
> ***Your Answer***
>
> Direct construction can reintroduce mixed-family kits or inconsistent defaults, for example an edge sensor combined with a simulation actuator. It also spreads creation rules into HTTP code. Our handler passes the requested family to DeviceFamilyService, which resolves the factory, creates the kit, and asks the repository to save it. A dedicated to_device_dto() mapper converts the saved domain devices into response DTOs. DTOs describe transferred data rather than select or construct domain products.

10. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?

> [!NOTE]
> ***Your Answer***
>
> Abstract Factory groups related products that must form a compatible family; it is not a general container for every creation operation. Locations, readings, and devices have different responsibilities and lifecycles. Combining them into one factory would increase coupling and make unrelated changes affect the same component. Our family factory should create matching sensor and actuator kits. Locations and readings should have their own creation processes, and devices can be assigned to locations separately.
