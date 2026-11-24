# Observer Pattern — Phase 11

## Intent

Observer lets one event notify multiple interested subscribers without
the publisher knowing their concrete implementations.

In this application, reading ingestion, command execution, and actuator
state transitions publish domain events. Subscribers decide whether
those events should produce persistent alerts.

## Participants

- Subject: EventBus.
- Publishers: ReadingIngest, CommandService, and ActuatorStateService.
- Events: ReadingCreated, ThresholdCrossed, CommandFailed, and
  ActuatorStateChanged.
- Subscribers: MoistureThresholdSubscriber and AlertPersistenceSubscriber.
- Persistence: AlertRepository and the PostgreSQL alerts table.
- Consumer: the dashboard EventFeed, which queries the alerts API.

The application uses its existing ActuatorStateService name for the
transition service described in the assignment.

## Event bus

EventBus provides subscribe(event_type, handler) and publish(event).

Handlers registered for an event's concrete class run in subscription
order. The subscription list is copied before dispatch, so a handler
added during notification starts receiving events on the next publish.

A subscriber exception is logged, and later subscribers still run.
There is no unsubscribe operation in this phase.

The shared bus is assembled in infrastructure/event_bus.py.
HTTP dependencies and the simulation sampler use this same instance.
Tests inject isolated buses and database sessions.

## Reading flow

Manual reads and automatic sampling both use ReadingIngest.record().
A translated reading can also be supplied to this method; this phase
does not add an MQTT client or a separate device readings route.

The ingest service validates and stores the reading. After a successful
insert and commit, it publishes ReadingCreated only if tracking_enabled
was true when the ingest checked the device.

The event includes device_id, value, unit, source, recorded_at,
location_id, and zone_id.

When tracking is off, an explicitly supplied reading can still be
stored, but ReadingCreated is not published. The automatic sampler
already selects tracked devices.

Unassigned devices publish null location_id and zone_id.

## Moisture rule

MoistureThresholdSubscriber handles ReadingCreated.

It publishes ThresholdCrossed only when:

- The unit is vwc.
- The event has a zone_id.
- The zone exists.
- The value is strictly below moisture_threshold_low.

A value equal to the threshold does not trigger an alert.
An unassigned reading does not produce a threshold event.

## Alert persistence

AlertPersistenceSubscriber saves these active alerts:

| Event | Severity | Message |
| --- | --- | --- |
| threshold.crossed | warning | Moisture below zone low |
| command.failed | warning | The command failure message |
| state.changed, only for error | critical | Actuator entered error |

Other actuator states do not produce alert rows.

The subscriber preserves the event's device, location, and zone IDs.
All three alert foreign keys are nullable and use ON DELETE SET NULL,
so deleting an associated record does not delete the alert.

The table also stores status, created_at, and acknowledged_at.
The API response does not include acknowledged_at.

## Command and state events

CommandService publishes CommandFailed after a failed command result
has been committed. State-rejected commands do not publish this event.

Successful command execution publishes ActuatorStateChanged when it
actually saves a different actuator state.

ActuatorStateService publishes ActuatorStateChanged after a successful
transition commit.

Publishers do not import AlertRepository and do not write alert rows.

## Transactions and limitations

Business data is committed before events are published.

Alert subscribers use separate database sessions. A failed alert insert
is rolled back and logged without rolling back the completed business
operation or blocking later subscribers.

This is a synchronous, in-process bus, not a durable message queue.
A process crash between business commit and publication can lose a
notification. Failed subscribers are not automatically retried.
Durable delivery would require additional infrastructure, such as an
outbox and retry processing.

Repeated readings below the threshold can create repeated alerts.
This phase does not implement deduplication or automatic resolution.

## API and dashboard

GET /api/alerts returns the newest alerts first.

- Default status: active.
- Accepted statuses: active, resolved, all.
- Invalid status: HTTP 400.
- Default limit: 50; allowed range: 1–200.
- Optional filters: location_id, zone_id, since.
- since includes alerts created at or after the supplied timestamp.
- Timestamps without a timezone are interpreted as UTC.

Scalar documents the endpoint.

EventFeed appears in #events and polls every five seconds.
It supports location and zone filters, severity badges, and an empty
state. Polling is cleaned up when the component unmounts.

Alerts survive page refresh because they are stored in PostgreSQL.

## Comparison with other patterns

Facade provides a simpler entry point for calling a subsystem.
The Phase 7 overview facade combines data for a request.
Observer distributes notifications after something happens.

Command represents an intention to act, such as stopping a pump.
Observer distributes the outcome, such as a command failure.
The command service publishes an event without knowing who stores alerts.

## Phase 12 handoff

services/realtime.ts exports RealtimeEvent and subscribeRealtime.
Its implementation is a no-op that returns an unsubscribe function.

Phase 12 can connect a dashboard WebSocket subscriber to the same event
system. AlertCreated is not implemented in this phase; it can be added
after successful alert persistence to carry the saved alert to that
subscriber.

The existing sensor readings poll remains in place.
No WebSocket connection or alert Resolve action is implemented here.

## Verification

The complete backend suite passed with 232 tests.

Phase 11 adds:

- Six event bus tests.
- Five reading publication tests.
- Sixteen alert subscriber and API tests.

Coverage includes subscriber ordering and failure isolation, tracking
on/off behavior, persistence, threshold boundaries, filtering, command
failure alerts, and error-state alerts.

Manual checks also verified a low-moisture alert, an error-state alert,
and an unassigned command-failure alert. Temporary actuator state and
assignment changes were restored after the checks.