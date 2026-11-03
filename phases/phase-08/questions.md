# Phase 8 — State questions

**Pattern / focus:** State.

**Read first:** [Guide 08](../../materials/guides/08-state.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example support-ticket states) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to actuator lifecycle, persisted state, and `allowed_commands` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of the State pattern in plain language. What problem appears when lifecycle is modelled as boolean flags and scattered `if` guards?

> [!NOTE]
> ***Your Answer***
>
> The State pattern makes an object's allowed behaviour depend on its current state. In my project, a running actuator allows different commands from an idle actuator. Many boolean flags and scattered checks can create conflicting states and make rules easy to miss.

2. Name the participants (**context**, **state interface**, **concrete states**, **client**). How does a successful command lead to a **transition**, and where do **guards** live?

> [!NOTE]
> ***Your Answer***
>
> My context is `ActuatorContext`. `ActuatorState` provides the shared operations, including `allowed_commands()` and `target_for()`. I use five configured state objects for idle, running, off, error, and maintenance instead of five separate classes. `ActuatorStateService` is the client of the context.
>
> The current state checks a command and returns its target state. The context then changes to that state. The guards live in the domain, while the service handles saving the result.

3. What is `allowed_commands` (or equivalent) for? Why is exposing “what can I do **now**?” better than letting the UI guess from a raw state string?

> [!NOTE]
> ***Your Answer***
>
> `allowed_commands` lists the commands that are legal in the current state. For example, running allows `stop` and `report_error`. The UI can use this list directly, so it does not need its own copy of the transition rules.

## B. This phase of the application

4. Which actuator states did you implement (for example idle, running, error)? Sketch the **legal** transitions (which command or event moves idle → running, running → idle, into error, and out of error).

> [!NOTE]
> ***Your Answer***
>
> I implemented idle, running, off, error, and maintenance.
>
> - idle: `start` → running, `turn_off` → off, `enter_maintenance` → maintenance, `report_error` → error.
> - running: `stop` → idle, `report_error` → error.
> - off: `turn_on` → idle, `enter_maintenance` → maintenance, `report_error` → error.
> - error: `reset` → idle, `enter_maintenance` → maintenance.
> - maintenance: `finish_maintenance` → idle, `report_error` → error.
>
> Other transitions are rejected. For example, running cannot change directly to maintenance.

5. Why is actuator state stored in `actuator_states` (or equivalent) rather than only in process memory? What must still be true after you restart the backend?

> [!NOTE]
> ***Your Answer***
>
> Process memory is lost when the backend restarts. The database keeps each actuator's saved state. After a restart, the API must return the same state and the correct allowed commands. I checked this by restarting the backend while the pump's saved state was running.

6. An **illegal** transition must raise a domain error and **must not** update the database. Why? Which HTTP status is reasonable for that case (400 or 409), and why should the rule live in the domain rather than in React?

> [!NOTE]
> ***Your Answer***
>
> An illegal transition breaks the lifecycle rules, so the previous state must stay unchanged. My domain raises `IllegalTransitionError`, and the service rolls back the transaction. The API returns HTTP 409 because the requested transition conflicts with the current state.
>
> The rule belongs in the domain because requests can come from clients other than React. Frontend checks alone cannot protect the saved state.

7. Device JSON gains `state` and `allowed_commands`. How does the dashboard use those fields (badges, disable illegal buttons)? How does this prepare **Phase 10 Command**?

> [!NOTE]
> ***Your Answer***
>
> My dashboard shows a coloured state badge and the allowed commands on actuator cards. These commands are currently labels, not clickable buttons. Sensors do not show actuator state information.
>
> In Phase 10, command buttons can be enabled only when their commands appear in this list. The backend must still check the current state before executing a command.

## C. Compare, contrast, and scenarios

8. Contrast State with **Strategy**. Both look like “context delegates to an object.” Who typically **changes** the active object, and is the variation a **lifecycle** or a **selectable policy**? Give a greenhouse example of each (this phase vs Phase 6).

> [!NOTE]
> ***Your Answer***
>
> State changes through lifecycle events or commands. In Phase 8, the actuator context moves from idle to running after a valid `start` command.
>
> Strategy is a selectable policy, usually chosen by a client or configuration. In Phase 6, the user selects conservative or aggressive irrigation for a location. Changing that policy does not change an actuator's lifecycle state.

9. Contrast State with a pile of booleans (`is_running`, `is_fault`, `is_maintenance`). Why do illegal combinations of flags appear, and how do explicit state objects (or a transition table) prevent that?

> [!NOTE]
> ***Your Answer***
>
> Separate flags can be changed independently, so an actuator might accidentally be marked as both running and in maintenance. My context holds one current state. Its transition rules allow only defined changes, which prevents those conflicting combinations when using the domain methods.

10. A classmate puts HTTP status mapping or SQLAlchemy commits **inside** a concrete state class. Another state mutates a flag directly and skips `transition` / `set_state`. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> Putting HTTP or database code inside a state class mixes lifecycle rules with infrastructure. It makes the state harder to test and reuse. In my project, the API maps errors to HTTP responses, and the service manages the transaction through the repository.
>
> Changing a flag directly skips the guards and can create an illegal state. State changes should go through the context methods so the rules are always checked.