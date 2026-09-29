# Builder — Phase 4

## What Builder does here

`LocationConfigBuilder` creates a location configuration step by step:

1. Set the location name.
2. Add one or more zones.
3. Call `build()` to check the complete configuration.

The result is an unsaved `LocationConfig` containing a location and its zones. The builder does not connect to the database. IDs are assigned when the repository saves the configuration.

## Why Builder fits this task

A location needs several pieces of information, including zones, moisture thresholds, and schedules. Builder lets these pieces be collected before checking the whole configuration.

Factory Method is about creating a particular product type. Abstract Factory creates related products from a matching family. Builder is used here because the task is to assemble one valid configuration in steps.

## Where validation lives

The domain builder and the shared functions in `validation.py` check:

- Location and zone names are not blank.
- Names do not exceed 128 characters.
- A new location has at least one zone.
- Zone names are unique within a location.
- Moisture thresholds are finite numbers between 0 and 1.
- The low threshold is strictly less than the high threshold.
- A schedule is a dictionary.

The same zone validation functions are reused when adding or editing saved zones. The database also has constraints for duplicate zone names and threshold values.

React checks input to give helpful feedback, but backend validation is still required. Invalid configurations must be rejected even when the request does not come from the dashboard.

## Request and save flow

The creation flow is:

Request DTO → application mapper → Builder → repository → response DTO.

If `build()` fails, the repository is not called.

The repository saves the location and its zones in one transaction. It uses `flush()` to obtain IDs and commits after all inserts succeed. A failure rolls back the transaction.

The domain classes do not import FastAPI, Pydantic, or SQLAlchemy.

## Why location_id is used

The course uses location as the database and API resource name. Each zone belongs to one location through `location_id`. The product is still a smart greenhouse application.

New tables and endpoints use this naming consistently rather than introducing `greenhouse_id`.

## Why device assignment is separate

Devices already exist, and assignment needs a saved zone ID. Therefore, the builder has no `add_device()` method.

A separate assignment service handles changes through:

`PATCH /api/devices/{id}/zone`

The client sends only `zone_id`. The backend copies the location ID from that zone and updates both fields in one transaction. Sending `null` clears both fields. An unassigned device remains valid.

## Managing saved locations and zones

Listing or deleting locations and adding, editing, or deleting saved zones do not call the builder.

The location list is ordered by creation time, newest first, with ID descending as a tie-breaker. Creating another location keeps earlier locations.

Deleting a location removes its zones and clears device assignments through the foreign keys. Device rows remain.

Deleting a zone explicitly clears both assignment fields before removing it. The last zone of a location cannot be deleted.

## Dashboard

The creation wizard collects a location name and a draft list of zones. It sends the complete configuration when the user clicks Create location.

The Configuration section loads saved locations from the API and supports zone management.

Device cards list zones from all saved locations, grouped by location. Labels use the format `Location name — Zone name`. The Unassigned option clears the assignment.

Changes trigger refreshes so the configuration section and device cards show updated data.

## Tests

Builder unit tests cover valid configurations, missing names, missing zones, invalid thresholds, duplicate zone names, and separation of mutable schedule data.

API tests cover configuration creation and reading, invalid input, location listing and deletion, zone management, device assignment, cancellation, and missing resources.

API tests use the separate `greenhouse_phase3_test` database. Each test runs inside a transaction that is rolled back afterward. This existing test database name is retained so Phase 3 tests can run alongside Phase 4 tests.

The migrations were also applied successfully to a newly created empty test database.