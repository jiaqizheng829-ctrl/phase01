# Phase 11 — Observer (Requirements)

This is the **assignment**. Implement from these requirements. If you get stuck or want to check your design, use the [guided check](guided-check.md) (signatures and partial snippets — not a complete solution).

After you implement, answer the [questions](./questions.md).

## Purpose

Introduce an in-process **event bus** (publish/subscribe). Persist **alerts** so the event feed survives refresh. Phase 12 will fan the same events out over WebSocket — do not implement WS here beyond a client **stub**.

## Scope and naming rules

- Publishers (reading ingest, command executor, state transitions) must not import UI or HTTP. They publish domain events. They must not import `AlertRepository`.
- Every successful ingest publishes `reading.created` with `device_id`, `value`, `unit`, `source`, `recorded_at`, and the device’s `location_id` and `zone_id`. Skip that publish when `tracking_enabled` is false (the row may still be stored). Manual read, the simulation sampler, and a translated MQTT payload all use this same publish rule.
- Two subscribers handle the rules. `MoistureThresholdSubscriber` listens for `reading.created`. `AlertPersistenceSubscriber` inserts alert rows. They do not read an MQTT socket. Do not add a broker client or the device readings route in this phase.
- `location_id` and `zone_id` are copied from the device when known. Both stay null when the device is unassigned. Do not invent a zone for an unassigned device. The seeded pump is unassigned, so a failed command on it stores both ids as null.

## Outcome required at end of phase

- Event bus with `MoistureThresholdSubscriber` and `AlertPersistenceSubscriber`.
- Ingest publishes `reading.created` only while that device’s `tracking_enabled` is true.
- A moisture reading strictly below the zone low creates an `alerts` row visible in the feed after poll. A failed command and a transition to `error` create the other two rows.
- `GET /api/alerts` lists alerts (default `status=active`, optional `since`, `location_id`, `zone_id`, and `limit`).
- Dashboard event feed in `#events` polls the API every 5 seconds. Sensor cards may keep the Phase 5 readings poll.
- `realtime.ts` interface exists as a stub for Phase 12.
- Scalar documents `GET /api/alerts`.
- Pattern note at `docs/patterns/observer.md`.

---

## Prerequisites

- Phase 10: commands and state changes to react to.
- Phase 5: ingest path (`ReadingIngest`) that already stores readings from manual read, the sampler, and MQTT translation.

---

## Required architecture for this phase

- **Domain:** event types (`ReadingCreated`, `ThresholdCrossed`, `CommandFailed`, `ActuatorStateChanged`); `EventBus` with `subscribe` and `publish`.
- **Application:** `MoistureThresholdSubscriber` and `AlertPersistenceSubscriber`. Publishers are `ReadingIngest`, `CommandService`, and `ActuatorTransitionService`. Ingest publishes `reading.created` after a successful insert when `tracking_enabled` is true.
- **Infrastructure:** `alerts` table + repository. Alert foreign keys are nullable and `ON DELETE SET NULL`.
- **API:** `GET /api/alerts`.
- **Frontend:** `EventFeed` polling `#events`; `realtime.ts` stub.

---

## Suggested file locations

Paths are relative to **`yourpath\project\`**.

```text
yourpath\project\
├── backend/src/
│   ├── domain/events/events.py           # ReadingCreated, ThresholdCrossed, CommandFailed, ActuatorStateChanged
│   ├── domain/events/bus.py              # EventBus: subscribe and publish
│   ├── application/alerts/subscribers.py # MoistureThresholdSubscriber, AlertPersistenceSubscriber
│   ├── application/alerts/dto.py
│   ├── infrastructure/persistence/models.py              # AlertRow
│   ├── infrastructure/persistence/alert_repository.py
│   └── interfaces/api/alerts.py
└── frontend/src/
    ├── services/realtime.ts              # stub until Phase 12
    └── components/alerts/EventFeed.tsx   # #events, poll every 5 seconds
```

## Type hints

Domain events (plain objects/dataclasses): include `device_id: UUID | None`, `location_id: UUID | None`, `zone_id: UUID | None`, and event-specific fields (e.g. moisture `float` on threshold crossed). Copy `location_id` and `zone_id` from the device at publish time.

ORM `alerts`:

| Column            | SQL hint                                              |
| ----------------- | ----------------------------------------------------- |
| `id`              | UUID PK                                               |
| `location_id`     | UUID FK, **nullable**, `ON DELETE SET NULL`           |
| `zone_id`         | UUID FK → `zones`, **nullable**, `ON DELETE SET NULL` |
| `device_id`       | UUID FK, **nullable**, `ON DELETE SET NULL`           |
| `severity`        | VARCHAR — `"info"` \| `"warning"` \| `"critical"`     |
| `message`         | TEXT                                                  |
| `event_type`      | VARCHAR (e.g. `threshold.crossed`, `command.failed`)  |
| `status`          | VARCHAR — `"active"` \| `"resolved"`                  |
| `created_at`      | timestamptz                                           |
| `acknowledged_at` | timestamptz, nullable                                 |

Alert DTO JSON: `{ id, location_id, zone_id, device_id, severity, message, event_type, status, created_at }`. The `acknowledged_at` column is stored and is not part of this response.

Frontend stub: `RealtimeEvent = { type: string; payload: unknown }`; `subscribeRealtime` returns an unsubscribe `() => void`.

---

## Step-by-step implementation requirements

## Step 1 — Database

`alerts`:

| Column            | Intent                                       |
| ----------------- | -------------------------------------------- |
| Identifier        | PK                                           |
| `location_id`     | FK, nullable, `ON DELETE SET NULL`           |
| `zone_id`         | FK → `zones`, nullable, `ON DELETE SET NULL` |
| `device_id`       | FK, nullable, `ON DELETE SET NULL`           |
| `severity`        | `info` / `warning` / `critical`              |
| `message`         | Text                                         |
| `event_type`      | e.g. `threshold.crossed`, `command.failed`   |
| `status`          | `active` / `resolved`                        |
| `created_at`      | Timestamptz                                  |
| `acknowledged_at` | Nullable                                     |

Optional extra table for append-only domain events is **not** required.

Autogenerate and apply.

Acceptance criteria:

- Schema uses `location_id` and nullable `zone_id` when those FKs are present. Neither is `greenhouse_id`.

## Step 2 — Bus and subscribers

- `EventBus` with `subscribe(event_type, handler)` and `publish(event)`. Handlers for one event class run in subscription order. This bus has no `unsubscribe`.
- `MoistureThresholdSubscriber` listens for `ReadingCreated`. It publishes `ThresholdCrossed` only when `unit` is `vwc`, `zone_id` is set, and `value` is strictly below that zone’s `moisture_threshold_low`. A reading with no zone does not publish a threshold event.
- `AlertPersistenceSubscriber` inserts one active `alerts` row:
  - `threshold.crossed`, severity `warning`, message `Moisture below zone low`
  - `command.failed`, severity `warning`, message from the failure (the max-run-time case is `Max run time exceeded`)
  - `state.changed`, severity `critical`, message `Actuator entered error`, and only when `ActuatorStateChanged.state` is `error`
- Optional `MetricsSubscriber` with no table.

Publish from: every successful ingest (`ReadingCreated` with `device_id`, `value`, `unit`, `source`, `recorded_at`, `location_id`, and `zone_id`), a command failure (`CommandFailed`), and every successful state save (`ActuatorStateChanged`). Do not publish `ReadingCreated` when `tracking_enabled` is false. Copy `location_id` and `zone_id` from the device. Both stay null when the device is unassigned.

Acceptance criteria:

- Publishers do not call the alerts repository directly (they publish).
- Subscriber insert is covered by a test.
- A sampler or `POST /read` on a tracked device publishes `reading.created`. The same ingest with tracking off stores the row and does not publish.

## Step 3 — API and UI

- `GET /api/alerts` returns a list, newest `created_at` first. Default `status=active` and `limit=50` (`limit` is 1–200). `status` may be `active`, `resolved`, or `all`; any other value is 400. Optional filters are `location_id`, `zone_id`, and `since` (`created_at` at or after `since`).
- Event feed in `#events` (`frontend/src/components/alerts/EventFeed.tsx`) polls `GET /api/alerts` every 5 seconds. The feed can filter to one location and one zone. Empty state.
- `frontend/src/services/realtime.ts`: export `RealtimeEvent` and `subscribeRealtime`, which returns an unsubscribe function. The Phase 11 body is a no-op. Comment that Phase 12 replaces it with the dashboard WebSocket. Leave the Phase 5 readings poll in place.

Acceptance criteria:

- Trigger a low moisture read on an assigned device (or seed) → new alert row with that `location_id` and `zone_id` → visible in the filtered feed after poll.
- An unassigned device’s alert leaves both ids null.
- Refresh still shows alerts (DB-backed).

## Step 4 — Tests and docs

- Subscriber inserts on published event.
- Ingest with tracking on publishes `reading.created`; tracking off does not.
- A moisture value of `0.10` on Bench 1 (low `0.20`) inserts `threshold.crossed`, and `GET /api/alerts?zone_id=` for that zone returns it. Another zone’s filter does not.
- A failed command on the unassigned seeded pump inserts `command.failed` with `location_id` and `zone_id` null.
- `POST` transition `target=error` inserts `state.changed` with severity `critical` and message `Actuator entered error`.
- `ReadingIngest`, `CommandService`, and `ActuatorTransitionService` do not import `AlertRepository`.
- `docs/patterns/observer.md`.

---

## Definition of done

- Bus with `MoistureThresholdSubscriber` and `AlertPersistenceSubscriber`.
- `reading.created` is published from ingest only when tracking is on.
- The three alert rows are `threshold.crossed` (warning), `command.failed` (warning), and `state.changed` (critical, only for `error`).
- `alerts.zone_id` is filled from the device when assigned, and null when it is not.
- `#events` polls `GET /api/alerts` every 5 seconds and can filter by location and zone. The readings poll may remain.
- `realtime.ts` stub is in place.
- Tests and pattern doc complete.

---

## Common pitfalls to avoid

- Fetching alerts inside the reading adapter (tight coupling).
- WebSocket implementation in this phase (belongs in Phase 12).
- Alerts only in React state.
- Publishing `reading.created` for a device with `tracking_enabled` false.
- Inventing a `zone_id` for an unassigned device.
- A separate publish path for the sampler versus `POST /read`.

---

## Handoff to next phases

- After each alert insert, the example publishes `AlertCreated` on the same bus. Phase 11 does not need a socket client for that event. Phase 12 subscribes a dashboard WebSocket to this bus and fans `AlertCreated` out. Phase 13 adds `PATCH /api/alerts/{id}` with `{ "status": "resolved" }`.
- Phase 12 also replaces the sensor-card readings poll while that socket is up, and may deliver readings on the device HTTP route or from an optional MQTT broker. Neither transport may become a second publisher; each calls ingest, which already publishes.

→ [Phase 12 — Production API, WebSocket, hardening (requirements)](../phase-12/requirements.md) · [guided check](../phase-12/guided-check.md)
