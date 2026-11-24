# Phase 11 鈥?Observer questions

**Pattern / focus:** Observer.

**Read first:** [Guide 11](../../materials/guides/11-observer.md) 路 [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example live auction bids) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to the event bus, alerts, publishers, and the event feed from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Observer in plain language. What is a **one-to-many** dependency here, and why must the subject notify dependents **without** knowing their concrete classes?

> [!NOTE]
> **_Your Answer_**
>
> Observer lets one event source notify several interested listeners. In this greenhouse, one published event can trigger alert persistence and later other listeners such as metrics. The publisher depends on the bus interface instead of concrete subscribers, so new listeners can be added without changing the publisher.

2. Name the participants (**subject / event bus**, **observer / subscriber**, **concrete observers**, **event**, **publisher**). What does `subscribe` / `unsubscribe` / `publish` (or `notify`) each do? This example鈥檚 `EventBus` implements `subscribe` and `publish` only.

> [!NOTE]
> **_Your Answer_**
>
> The subject is EventBus. A subscriber is a registered handler, and the concrete observers include MoistureThresholdSubscriber and AlertPersistenceSubscriber. Events carry information about something that happened. Publishers include ReadingIngest, CommandService, and ActuatorStateService. subscribe registers a handler, unsubscribe would remove one, and publish delivers an event to matching handlers. Our bus implements subscribe and publish only.

3. When should you use Observer, and when should you skip it (only one listener forever; or you need a strict multi-step workflow with guaranteed order)?

> [!NOTE]
> **_Your Answer_**
>
> Observer is useful when several independent reactions may follow the same event and those reactions can change over time. A direct call is simpler when there will only ever be one listener. For a strict multi-step workflow with required dependencies, rollback, and guaranteed completion, I would use explicit orchestration. Registration order in our bus does not provide those workflow guarantees.

## B. This phase of the application

4. Give at least two **domain events** you publish in this lab, including `reading.created` (only when `tracking_enabled` is true), a threshold-crossed event, command-failed, and `ActuatorStateChanged`. The persistence subscriber stores `state.changed` only when that state is `error`. Who publishes `reading.created`, and why do a manual read, the simulation sampler, and MQTT translation share that one ingest publish? Why must a publisher **not** import the alerts repository or the UI?

> [!NOTE]
> **_Your Answer_**
>
> Our events include reading.created, threshold.crossed, command.failed, and state.changed represented by ActuatorStateChanged. ReadingIngest publishes reading.created after storing a reading, only when tracking_enabled is true. Manual reads and the simulation sampler use this shared ingest path; translated MQTT readings should also enter through record rather than publish separately. This keeps validation and event publication in one place. MoistureThresholdSubscriber publishes threshold.crossed for a vwc reading strictly below the assigned zone's low threshold. CommandService publishes execution failures, and state changes are published after successful persistence. Only an error state creates a state-change alert. Publishers must not import the alerts repository or UI because their job is to report events, not decide every reaction.

5. What does `AlertPersistenceSubscriber` (or your equivalent) do when it handles an event? Name the three stored rows: `threshold.crossed` / `warning` / `Moisture below zone low`, `command.failed` / `warning` / the failure message, and `state.changed` / `critical` / `Actuator entered error`. Why do alerts live in the `alerts` table so the event feed still shows them after a **refresh**?

> [!NOTE]
> **_Your Answer_**
>
> AlertPersistenceSubscriber converts selected events into persistent alerts through an injected save callback. It stores threshold.crossed with warning severity and the message 'Moisture below zone low'; command.failed with warning severity and the original failure message; and state.changed with critical severity and 'Actuator entered error', only for the error state. The callback writes to PostgreSQL. Keeping alerts in the alerts table lets a new API request retrieve them after a browser refresh or backend restart, instead of depending on temporary browser memory.

6. The dashboard Event feed **polls** `GET /api/alerts` every 5 seconds in this phase. `services/realtime.ts` is only a **stub**. Why is full WebSocket **not** required in this phase? What should Phase 12 plug into so you do **not** re-implement pub/sub inside socket handlers? Phase 12 subscribes a dashboard socket to this same bus, and the example publishes `AlertCreated` after each insert for that socket.

> [!NOTE]
> **_Your Answer_**
>
> Full WebSocket support is outside Phase 11. Polling GET /api/alerts every five seconds already lets the dashboard display persisted alerts. services/realtime.ts is a no-op subscription stub for the later implementation. Phase 12 should attach its socket delivery subscriber to the existing event bus instead of creating another pub/sub system in socket handlers. An AlertCreated event published after a successful alert insert can carry the saved alert to that subscriber; this event and socket delivery are not implemented in my Phase 11 version.

7. Describe the must-demo path: a **tracked** low-moisture reading leads to an alert row that appears in the feed after poll. Which objects collaborate (reading pipeline 鈫?bus 鈫?subscriber 鈫?API 鈫?UI), and which object must **not** write the alert directly? What is stored, and what is not published, when `tracking_enabled` is false?

> [!NOTE]
> **_Your Answer_**
>
> A tracked low-moisture reading is stored by ReadingIngest, which publishes ReadingCreated. EventBus delivers it to MoistureThresholdSubscriber. That subscriber checks the zone's low threshold and publishes ThresholdCrossed. AlertPersistenceSubscriber then saves the warning through its persistence callback. GET /api/alerts returns the row, and EventFeed displays it on its next poll. ReadingIngest must not write the alert directly. If tracking_enabled is false, a reading explicitly passed into ingest is still stored, but no ReadingCreated event is published, so this path does not trigger a threshold alert. The automatic sampler skips sensors whose tracking is disabled.

## C. Compare, contrast, and scenarios

8. Contrast Observer with **Facade**. Facade simplifies **calling into** a subsystem. Observer **fans out** notifications after something happened. How do both appear in this greenhouse (Phase 7 overview vs this phase)?

> [!NOTE]
> **_Your Answer_**
>
> Facade offers a simpler entry point for requesting work or data from several parts of a subsystem. The Phase 7 overview combines greenhouse information for the dashboard through one interface. Observer distributes notifications to interested listeners after something happens. In Phase 11, publishers emit events and subscribers react independently. A facade answers a request; an observer receives a notification.

9. Contrast Observer with **Command**. Command captures **intent to act**. Observer propagates **outcomes**. How can `execute()` publish an event without the command class knowing who persists alerts?

> [!NOTE]
> **_Your Answer_**
>
> Command represents an action to perform, such as starting a pump. Observer communicates an outcome, such as a failed execution or a saved state change. In my implementation, CommandService invokes the command and publishes the outcome through the injected event bus after committing the result. The command class only uses its actuator port and does not need to know that an alert persistence subscriber exists.

10. One subscriber throws during `notify` / `publish` and aborts the loop, so later subscribers never run. Why is that a trap? What should the bus do so a failing alert writer does not block metrics (or later WebSocket) subscribers?

> [!NOTE]
> **_Your Answer_**
>
> If one subscriber exception aborts the loop, unrelated listeners miss the event and behavior depends on which listener failed first. Our bus catches and logs exceptions around each handler, then continues with the remaining handlers in registration order. The alert persistence callback rolls back its own failed database transaction. This keeps an alert writer failure from blocking later listeners, but it does not retry the failed handler or guarantee durable event delivery.
