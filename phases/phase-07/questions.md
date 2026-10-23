# Phase 7 — Facade questions

**Pattern / focus:** Facade.

**Read first:** [Guide 07](../../materials/guides/07-facade.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a video publish pipeline) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to the location overview, the facade, and the dashboard Overview page from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Facade in plain language. What problem appears when every HTTP handler (or every UI screen) repeats the same multi-step dance across repositories and services?

> [!NOTE]
> **_Your Answer_**
>
> Facade gives one simple entry point to several parts of the application. Without it, different routers or pages would repeat the same steps to load and combine data. That repeated code would be harder to maintain and could behave differently in different places.

2. A facade **orchestrates** collaborators. What should it **not** become (a god object that owns all domain logic)? Where should irrigation policy, sensor translation, and persistence stay instead?

> [!NOTE]
> **_Your Answer_**
>
> The facade should coordinate other classes, not do everything itself. Irrigation policies stay in the strategy classes, sensor translation stays in adapters, and database queries stay in repositories. My facade combines their results into the overview response.

3. When should you use Facade, and when should you skip it (a single repository call is enough; or you actually need to **translate** a mismatched interface)?

> [!NOTE]
> **_Your Answer_**
>
> I would use Facade when a task needs several repositories or services working together. If one simple repository call is enough, a facade may be unnecessary. If I need to make an incompatible interface work with my application, I would use Adapter instead.

## B. This phase of the application

4. What does `GET /api/locations/{location_id}/overview` return? Name the main pieces of the overview DTO: location, assigned device counts, and `zones` (thresholds, assigned devices, and those devices’ latest readings, including `tracking_enabled` and `sampling_interval_seconds`), plus strategy key and last recommendation. Why may those reading rows come from the sampler or MQTT ingest, not only from `POST /read`? Why is overview scoped by `location_id`?

> [!NOTE]
> **_Your Answer_**
>
> It returns the location ID and name, assigned sensor and actuator counts, and all zones. Each zone includes its thresholds, assigned devices, and their latest readings. Reading summaries also include tracking_enabled and sampling_interval_seconds from the device.
>
> The response includes the saved strategy key and a recommendation calculated through the automation service. If no strategy is saved, both fields are null.
>
> Manual reads, the sampler, and MQTT ingest all save readings in the same table, so overview can use any of them. The location_id keeps the response limited to the selected location and its zones.

5. Why does this phase **not** require a new business table? What already exists from Phases 2–6 that the facade only **composes**?

> [!NOTE]
> **_Your Answer_**
>
> The data is already stored in locations, zones, devices, sensor_readings, and automation_rules. The facade reads and combines it. The recommendation is calculated when overview is requested, so I do not need a new table to store it.

6. The overview HTTP handler should call **only** the facade, not reading/strategy/device repositories directly. Why? How does that help tests and later changes to the query shape?

> [!NOTE]
> **_Your Answer_**
>
> This keeps the handler focused on HTTP input and output. The facade handles the steps needed to build the overview. I can test that work separately and change repository queries without rewriting the handler, as long as the response stays the same.

7. The location selector may use the existing locations list. The Overview cards come from **one** overview fetch, and Refresh repeats that same fetch. Why must the React page not stitch device, reading, and automation calls together to build the same snapshot? How does a new reading or a saved strategy show up on overview without extra frontend glue?

> [!NOTE]
> **_Your Answer_**
>
> Combining separate responses in React would repeat the backend's work and require more requests and error handling. My panel gets all card data from one overview response.
>
> When I click Refresh, the backend reads the database again and calculates the recommendation using the saved strategy. New readings and changed strategy settings then appear in the response.

## C. Compare, contrast, and scenarios

8. Contrast Facade with **Adapter**. One makes an existing interface usable; the other makes a subsystem simpler to call. Which is which, and how do both appear in this greenhouse app (Phase 5 vs Phase 7)?

> [!NOTE]
> **_Your Answer_**
>
> Adapter makes an incompatible interface usable. In Phase 5, my sensor adapters translate external data into the Reading format.
>
> Facade makes several subsystems simpler to call. In Phase 7, LocationOverviewFacade gives one entry point for location details, devices, readings, and automation results.

9. This phase mentions **N+1** queries. What is an N+1 problem in an overview that lists latest readings for many devices, and what can the facade (or its repository) do about it without putting SQL in the router?

> [!NOTE]
> **_Your Answer_**
>
> An N+1 problem would happen if I loaded the devices once and then ran a separate reading query for every device. More devices would mean more database queries.
>
> My repository uses one query to get the newest reading for all assigned device IDs, using row_number() grouped by device. The SQL stays in the repository. The existing automation service still performs its own per-zone moisture lookups.

10. A classmate hides every error behind a generic “overview failed,” so a missing location, a DB outage, and a strategy error look the same. Why is that a trap for a facade?

> [!NOTE]
> **_Your Answer_**
>
> These problems need different responses. A missing location should return 404, but a database outage does not mean the location is missing. Hiding everything behind one error makes debugging harder.
>
> My handler maps the specific missing-location error to 404. It does not turn other failures into that error. Having no saved strategy is normal and returns 200 with null strategy fields.