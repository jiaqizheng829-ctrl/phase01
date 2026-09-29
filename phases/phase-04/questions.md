# Phase 4 — Builder questions

**Pattern / focus:** Builder.

**Read first:** [Guide 04](../../materials/guides/04-builder.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example ramen orders) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to locations, zones, `location_id`, and the configuration wizard from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Builder in plain language. Why does construction of a complex object need **stepwise assembly** and **validation at the end** (`build()`), instead of a telescoping constructor or a half-filled dict written straight to the database?

> [!NOTE]
> **_Your Answer_**
>
> Builder helps create an object one step at a time. In this project, I first set the location name and then add its zones. When I call `build()`, it checks whether the whole configuration is valid.
>
> This is easier to follow than putting many arguments into one constructor. It also avoids saving an unfinished dictionary to the database. Some rules, such as requiring at least one zone and checking duplicate names, need the full configuration.

2. Name the main participants (**product**, **builder**, **optional director**, **client**). Until `build()` succeeds, is the intermediate object a finished domain product? Why does that distinction matter?

> [!NOTE]
> **_Your Answer_**
>
> The product is `LocationConfig`, which contains a location and its zones. The builder is `LocationConfigBuilder`. The application mapper is the client that calls the builder methods, and the service handles the overall process. I do not have a separate director; it would be an optional class that organizes the building steps.
>
> Before `build()` succeeds, the collected data is still a draft. It may have missing or incorrect values, so it should not be treated as a finished configuration or saved yet.

3. List at least three kinds of invalid configuration a location/zone `build()` should reject in **this** lab (name, zones, moisture thresholds). Why must those rules live in the **domain** builder, not only in the HTTP layer?

> [!NOTE]
> **_Your Answer_**
>
> It should reject a missing location name, no zones, empty zone names, and duplicate zone names within the same location. It should also reject moisture values outside 0–1 or a low value that is equal to or greater than the high value.
>
> These rules belong in the domain because the builder might be used without an HTTP request, for example in a test or script. My builder uses shared validation functions so the same rules can also be used when editing saved zones.

## B. This phase of the application

4. What aggregate does the builder produce (location plus zones)? Why does this course use **`location_id`** (and never `greenhouse_id`) as the name for that scope?

> [!NOTE]
> **_Your Answer_**
>
> It produces one `LocationConfig` containing a location and all its zones. At this point it is not saved, so the IDs are still `None`.
>
> The course uses location as the resource name in the database and API. Using `location_id` everywhere keeps the names consistent and makes it clear which location a zone belongs to. The application is still about smart greenhouses.

5. Describe the path from API request to persistence: DTO → builder steps → `build()` → repository. What must **not** be persisted if `build()` raises `ConfigurationError` (or equivalent)? Why does assigning a device wait until the zone row exists, and why does the client send only `zone_id`?

> [!NOTE]
> **_Your Answer_**
>
> The API receives a request DTO. The mapper uses its values to set the location name, add zones, and call `build()`. If this succeeds, the service asks the repository to save the configuration. The saved data is then converted into a response DTO.
>
> If `build()` raises `ConfigurationError`, no location or zones from that request should be saved. Device assignment happens later because it needs the ID of a zone that already exists. The client sends only `zone_id`, and the backend gets the correct `location_id` from that zone. When unassigning a device, both fields are cleared.

6. Saving a location and its zones must be **one transaction**. What goes wrong if the location row commits and a later zone insert fails? How does that relate to “no half-built aggregates in the database”?

> [!NOTE]
> **_Your Answer_**
>
> If the location is committed first and saving a zone fails, the database could contain a location with only some of its zones, or none. The result would be incomplete.
>
> My repository saves them in one transaction. It uses `flush()` to get the IDs, but commits only after all the inserts succeed. If something fails, it rolls back the writes. This means the whole configuration is saved together instead of leaving half of it in the database.

7. The configuration wizard UI collects fields in steps. How does that UI map to Builder without turning React (or the HTTP handler) into the place that owns domain validation?

> [!NOTE]
> **_Your Answer_**
>
> The wizard asks for the location name first, then lets the user add zones to a draft list. Clicking Create location sends this data to the backend, where the mapper calls the Builder.
>
> The UI checks basic mistakes so the user gets quick feedback. However, the backend still checks the rules itself. The HTTP handler calls the service and returns errors when needed. This means someone sending a request directly cannot skip the domain validation.

## C. Compare, contrast, and scenarios

8. Contrast Builder with Factory Method and with Abstract Factory. Which pattern answers “which type?”, which answers “which matching kit?”, and which answers “how do we assemble one **valid whole** in steps?”

> [!NOTE]
> **_Your Answer_**
>
> Factory Method is about “which type?” Different creators can create different products, such as moisture or light sensors.
>
> Abstract Factory is about “which matching kit?” It creates related devices from one family, such as simulation sensors and actuators.
>
> Builder is about “how do we assemble one valid whole in steps?” In this phase, it puts the location name and zones together and checks that the configuration is valid before it is saved.

9. Fluent method chaining (`builder.add_zone(...).build()`) is a coding style. Why is a fluent interface **not** the same thing as the Builder pattern?

> [!NOTE]
> **_Your Answer_**
>
> Method chaining lets me write several calls together because a method returns an object for the next call. This can make the code convenient to read, but chaining alone does not make something a Builder.
>
> A Builder collects the parts of an object and produces the result when construction is finished. I could call its methods on separate lines and it would still be a Builder. In my code, returning `self` just allows the chained style.

10. A classmate validates thresholds only in FastAPI / Pydantic and leaves `build()` empty. Another mutates builder fields after `build()` while treating the product as immutable. Explain why each is a trap.

> [!NOTE]
> **_Your Answer_**
>
> The first approach only protects the HTTP request. If another part of the program calls the builder directly, invalid thresholds could get through. This is why `build()` must check the domain rules too.
>
> The second approach can cause problems if the builder and finished product share the same mutable data. Changing the builder could then change something that was already built and checked. My builder creates new objects and deep-copies the schedule dictionaries to keep them separate.
>
> I also use frozen dataclasses, but this does not make the dictionaries inside them fully immutable. A caller could still change the finished product's own schedule. The copies prevent shared-state changes; they do not freeze the dictionary itself.