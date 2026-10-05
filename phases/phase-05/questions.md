# Phase 5 — Adapter questions

**Pattern / focus:** Adapter.

**Read first:** [Guide 05](../../materials/guides/05-adapter.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a legacy XML calendar client) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensor ports, adapters, readings, and `sensor_readings` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Adapter in plain language. What problem appears when business code speaks a vendor or legacy protocol (odd field names, units, XML, status codes) directly?

> [!NOTE]
> ***Your Answer***
>
> Adapter makes an existing interface work with the interface our application expects. I think of it as a translator between two parts of the program.
>
> Without it, business code would need to understand each vendor's field names, units and error codes. Changing a vendor could then require changes in several places instead of just one adapter.

2. Name the participants (**target / port**, **adaptee**, **adapter**, **client**). What does the adapter translate, and what must it **not** decide (business policy)?

> [!NOTE]
> ***Your Answer***
>
> The target is `SensorPort`, which defines the interface our application uses. The adaptee is the driver with a different interface, such as `VendorStubClient`. `VendorStubSensorAdapter` wraps that driver and translates its result. The client is `ReadingIngest`, which uses the sensor port.
>
> The adapter translates fields and units, such as a vendor's 41 percent moisture into 0.41 vwc. It should not decide whether a zone needs watering. That is a business decision.

3. GoF distinguishes an **object adapter** (composition) from a **class adapter** (inheritance). Which does modern code prefer, and why?

> [!NOTE]
> ***Your Answer***
>
> Modern code usually prefers an object adapter. It holds a reference to the object it adapts instead of inheriting from the vendor class. This makes it easier to replace the driver or pass in a fake driver for testing.
>
> My vendor adapter receives a client object in its constructor. It inherits from `SensorPort`, but it uses composition for the vendor client, so it is an object adapter.

## B. This phase of the application

4. What is `SensorPort` in this lab, and what normalized value type (for example `Reading`) do adapters return? Why do application services depend on the port rather than on a simulation driver or vendor SDK?

> [!NOTE]
> ***Your Answer***
>
> `SensorPort` is the shared interface with a `read(device)` method. Its adapters return a `Reading` containing the device ID, value, unit, source and a timestamp with a timezone.
>
> The application service can use this interface without knowing how each driver gets its data. For example, both simulation and vendor readings go through the same saving code. A new driver mainly needs a new adapter and a selector update.

5. You need three translations onto the same normalized reading: a simulation adapter, a vendor stub, and an MQTT translator that accepts a payload dict. Why is the different raw shape the point of the exercise? How does `source` (`simulation`, `vendor`, or `mqtt`) show which adapter produced the reading, and why must the MQTT translator not open a broker in this phase? Phase 12 may deliver that same dict on a device HTTP route or through an optional broker — why must this phase still not open either transport?

> [!NOTE]
> ***Your Answer***
>
> The different raw shape shows why an adapter is useful. My vendor stub returns `measurement`, `measurement_unit` and `status_code`. The adapter checks these and turns them into the same `Reading` used by the simulation adapter. For moisture, it also converts percent into vwc.
>
> The `source` field tells us which adapter produced the reading, and the sensor card displays it. The MQTT translator accepts a dictionary and returns a reading with `source="mqtt"`.
>
> This phase is about translating and storing data, not delivering it over a network. Keeping HTTP and broker connections out makes the translator easy to test with a dictionary. Phase 12 can deliver that dictionary through either transport and reuse the same translation and saving code.

6. Readings are **appended** to `sensor_readings` (history grows). Why not keep only the latest value in memory or overwrite a single row, and which later phase consumes this history? Why do a manual read, the simulation sampler, and (later) MQTT share **one** writer of that table? Why does the sampler skip devices with tracking off and MQTT devices, and why do sensor cards poll the latest stored reading until Phase 12?

> [!NOTE]
> ***Your Answer***
>
> Keeping readings only in memory would lose them when the backend restarts. Overwriting one row would keep the latest value but lose earlier measurements. Appending rows lets us keep history. Phase 6 uses the latest stored moisture reading for the correct zone, and optional Phase 13 charts can use readings over time.
>
> Manual reads, automatic sampling and MQTT use `ReadingIngest.record()` so the same checks and saving process apply to all of them. Later, this also gives us one place to publish reading events.
>
> Tracking off means automatic sampling should stop. MQTT devices are skipped because their readings should come from incoming device data, not from our simulation generator. The cards temporarily poll the database-backed API so automatic readings appear on screen. Phase 12 will replace this polling with WebSocket updates.

7. `POST /api/sensors/{id}/read` runs an adapter, persists, and returns a DTO. What HTTP status is appropriate when the device is missing versus when the adapter fails? Why must the router never see vendor-shaped types?

> [!NOTE]
> ***Your Answer***
>
> A missing device returns 404. An adapter or reading validation failure returns 400 with an explanation, as required in this phase. A successful read returns 201 because it creates a saved reading.
>
> The router should use the application service and normalized DTOs. If it understood vendor fields directly, changing a driver could also require changing the HTTP code.

## C. Compare, contrast, and scenarios

8. Contrast Adapter with **Facade**. Adapter changes the **shape** of an existing interface; Facade simplifies **how to use** a subsystem. Give a greenhouse-shaped example of each (Adapter this phase; Facade in Phase 7).

> [!NOTE]
> ***Your Answer***
>
> Adapter makes an incompatible interface fit the interface we need. In this phase, the vendor adapter converts a percentage and vendor field names into our `Reading` format.
>
> Facade gives the caller a simpler way to use several parts of a system. A greenhouse facade in Phase 7 could provide one operation to get a zone overview instead of making the caller separately load the zone, its devices and their latest readings. It simplifies those steps rather than translating a vendor format.

9. Contrast Adapter with **Decorator**. Both wrap an object. What is different about the interface they present to the client?

> [!NOTE]
> ***Your Answer***
>
> Adapter presents the interface the client needs when the wrapped object's interface is different. Decorator keeps the same interface and adds behavior around the wrapped operation.
>
> For example, the vendor adapter translates `fetch()` results into `SensorPort.read()` results. A future actuator decorator could keep `ActuatorPort.apply()` and add logging before forwarding the command to the wrapped actuator.

10. A classmate puts irrigation policy (“if moisture &lt; 0.3 then water”) inside the vendor adapter. Why is that a trap? Where should that decision live instead (later Strategy), and what should stay in the adapter?

> [!NOTE]
> ***Your Answer***
>
> That would mix reading a device with deciding how to manage the greenhouse. Different vendors could end up making different watering decisions, and changing a zone's rules would require editing driver code.
>
> The decision should belong to the later Strategy logic, using the zone's thresholds and readings. The adapter should translate the driver's data into a valid reading. An actuator adapter should apply a command it receives, rather than decide for itself when watering is needed.