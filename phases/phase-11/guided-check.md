# Phase 11 — Observer (Guided check)

Complete the [requirements](requirements.md) first. Use this document if you are stuck or to check signatures and JSON. Snippets are **not** a complete solution.

## Pattern

**Observer** — `EventBus` + subscribers (in-process). WebSocket is Phase 12.

---

## Target layout

```text
domain/events/
  events.py             # ReadingCreated, ThresholdCrossed, CommandFailed, ActuatorStateChanged
  bus.py                # EventBus: subscribe and publish
application/alerts/
  subscribers.py        # MoistureThresholdSubscriber, AlertPersistenceSubscriber
  dto.py
infrastructure/persistence/
  models.py             # AlertRow
  alert_repository.py
interfaces/api/alerts.py
frontend/src/components/alerts/EventFeed.tsx   # #events
frontend/src/services/realtime.ts              # stub until Phase 12
```

---

## Step 1 — Database

```text
alerts(
  id,
  location_id FK NULL ON DELETE SET NULL,
  zone_id FK NULL ON DELETE SET NULL,
  device_id FK NULL ON DELETE SET NULL,
  severity, message, event_type, status, created_at, acknowledged_at NULL
)
```

```powershell
alembic revision --autogenerate -m "alerts"
alembic upgrade head
```

**Check:** table exists; `location_id` and `zone_id` FKs are valid (not `greenhouse_id`). `zone_id` is nullable.

---

## Step 2 — Bus and subscribers

```python
class EventBus:
    def subscribe(self, event_type: type, handler: Callable) -> None: ...
    def publish(self, event: object) -> None: ...

class MoistureThresholdSubscriber:
    # unit == "vwc", zone_id set, value strictly below zone.moisture_threshold_low.
    # Then publish ThresholdCrossed. No zone means return.
    def on_reading(self, event: ReadingCreated) -> None: ...

class AlertPersistenceSubscriber:
    def on_threshold(self, event: ThresholdCrossed) -> None: ...
    def on_command(self, event: CommandFailed) -> None: ...
    # Insert only when event.state == "error".
    def on_state(self, event: ActuatorStateChanged) -> None: ...
```

**Publish sites** (application services, not routers):

- After a persisted ingest (manual read, sampler, or MQTT translation) → `ReadingCreated` with `device_id`, `value`, `unit`, `source`, `recorded_at`, `location_id`, and `zone_id`. Skip publish when `tracking_enabled` is false.
- `MoistureThresholdSubscriber` → `ThresholdCrossed` when the rule above matches.
- After a command failure → `CommandFailed`. The message is the exception text (`Max run time exceeded` when max run time blocks `stop_pump`).
- After every successful state save → `ActuatorStateChanged`. The persistence subscriber inserts `state.changed` only for `state == "error"`.

`location_id` and `zone_id` are copied from the device. Both stay null when the device is unassigned. The seeded pump is unassigned.

**Composition root:** construct one `EventBus`, subscribe both handlers, and inject that same bus into reading, command, and transition services. Publishers must **not** import `AlertRepository`.

Inserted rows:

- `threshold.crossed`, `warning`, `Moisture below zone low`
- `command.failed`, `warning`, the failure message
- `state.changed`, `critical`, `Actuator entered error`

**Check:** a tracked moisture reading of `0.10` on Bench 1 (low `0.20`) inserts an `alerts` row without the reading router calling the alerts repo. Tracking off stores the reading and does not publish `ReadingCreated`.

---

## Step 3 — API and UI

`GET /api/alerts?status=active&location_id=&zone_id=&since=&limit=50`

Newest `created_at` first. Default `status` is `active` and default `limit` is `50` (1–200). `status` may be `active`, `resolved`, or `all`; anything else is 400. `since` keeps rows with `created_at` at or after that time.

```json
{
  "id": "<uuid>",
  "location_id": "<uuid>",
  "zone_id": "<uuid>",
  "device_id": "<uuid>",
  "severity": "warning",
  "message": "Moisture below zone low",
  "event_type": "threshold.crossed",
  "status": "active",
  "created_at": "..."
}
```

`acknowledged_at` is a column. This response does not include it. Do not add `POST /api/alerts/{id}/ack` in this phase. Resolve is `PATCH /api/alerts/{id}` in Phase 13.

UI: `EventFeed` in `#events` polls every 5 seconds. It can filter to one location and one zone, and it has an empty state. Badge by severity. Tailwind. `realtime.ts` stays a stub. The live socket and the Resolve button are later phases.

**Check:** Scalar shows GET. A Bench 1 moisture reading of `0.10` increases the list for that `zone_id` after the poll.

---

## Step 4 — Tests and docs

Cover these cases:

- Tracking on publishes `ReadingCreated`. Tracking off stores the row and does not publish.
- Moisture `0.10` on Bench 1 inserts `threshold.crossed`, and `zone_id` for Bench 1 returns that row only.
- A failed `stop_pump` on the unassigned seeded pump inserts `command.failed` with `location_id` and `zone_id` null and message `Max run time exceeded`.
- `POST` transition `target=error` inserts `state.changed`, severity `critical`, message `Actuator entered error`.
- `ReadingIngest`, `CommandService`, and `ActuatorTransitionService` do not import `AlertRepository`.
- `docs/patterns/observer.md`: subject vs subscribers, vs Phase 12 WebSocket.

---

## Phase 11 completion checklist

- [ ] Bus with both subscribers
- [ ] Three alert rows persisted (`threshold.crossed`, `command.failed`, `state.changed`)
- [ ] `GET /api/alerts` plus `#events` polling every 5 seconds
- [ ] Publishers do not write alerts directly
- [ ] Tests + pattern doc

---

## Troubleshooting

| Symptom                            | Fix                                  |
| ---------------------------------- | ------------------------------------ |
| Alerts only from the alerts router | Publish from application services    |
| Reading service imports AlertRow   | Inject EventBus; subscriber persists |
| No events after HTTP success       | Call `bus.publish` after persist     |
| Live WS in this phase              | Poll or stub; sockets are Phase 12   |

---

## Next

→ [Phase 12 — API & WebSocket (requirements)](../phase-12/requirements.md) · [guided check](../phase-12/guided-check.md)
