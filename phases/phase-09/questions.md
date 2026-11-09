# Phase 9 — Decorator questions

**Pattern / focus:** Decorator.

**Read first:** [Guide 09](../../materials/guides/09-decorator.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example HTTP client wrappers) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to `ActuatorPort`, policy decorators, and `actuator_execution_log` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Decorator in plain language. Why is stacking wrappers a flexible alternative to a combinatorial explosion of subclasses (`LoggingRetryMaxRuntimeActuator`, …)?

> [!NOTE]
> ***Your Answer***
>
> Decorator adds behaviour by wrapping an object. I can combine separate wrappers instead of creating a new subclass for every combination of logging, retry and runtime checks.

2. Name the participants (**component**, **concrete component**, **decorator**, **concrete decorators**). What interface does every decorator present to the caller, and why must that match the wrapped component?

> [!NOTE]
> ***Your Answer***
>
> The component is ActuatorPort, and the concrete component is SimulationActuatorAdapter. The decorator role is a wrapper that implements ActuatorPort and holds an inner ActuatorPort. My concrete decorators are LoggingDecorator and MaxRunTimeDecorator.
>
> They all use apply(device_id, command, payload) and return None. Keeping the same interface lets one wrapper replace or wrap another.

3. **Order matters.** Using logging and retry (or logging and max-run-time) as an example, explain how wrapping A around B can change what you observe compared with wrapping B around A.

> [!NOTE]
> ***Your Answer***
>
> I put logging outside the runtime check. Logging can then catch a blocked attempt and save its failure. If the runtime check were outside logging, it could reject the request before logging was called.

## B. This phase of the application

4. What is `ActuatorPort` here, and which **at least two** decorators did you stack around the real adapter (for example logging and max run-time)? Where is the chain wired (composition root / factory), and why not inside the HTTP router?

> [!NOTE]
> ***Your Answer***
>
> ActuatorPort is the common interface for applying actuator commands. My chain is LoggingDecorator -> MaxRunTimeDecorator -> SimulationActuatorAdapter.
>
> ActuatorExecutionService builds the chain. This keeps policy setup out of the HTTP router and allows the service to be used directly in tests and scripts.

5. Max run-time can **short-circuit**: the inner adapter is never called. Why must a blocked attempt still produce a row in `actuator_execution_log` with `success=false` and the policy named in `policy_applied`?

> [!NOTE]
> ***Your Answer***
>
> A blocked request is still an execution attempt. Without a record, the user would not know why nothing happened. My log stores success=false, policies ["maxRunTime", "logging"], and the message "Max run time exceeded".

6. How does max run-time know the actuator has been running too long (for example `actuator_states.updated_at` from Phase 8)? Why is that data from **State**, not something the decorator should invent as a second lifecycle?

> [!NOTE]
> ***Your Answer***
>
> It reads state and updated_at from actuator_states. If the state is running and at least 30 minutes have passed, it blocks the request.
>
> Phase 8 already manages the lifecycle. Reusing its saved data avoids having two separate states or timers that could disagree.

7. `GET /api/actuators/executions` feeds the dashboard execution log. Why persist attempts in the database instead of only printing to stdout? What should the UI show after a blocked attempt and a refresh?

> [!NOTE]
> ***Your Answer***
>
> Database records remain available after a request or backend restart and can be loaded by the dashboard. Printing to stdout alone does not provide this history through the API.
>
> After a blocked attempt and refresh, the UI should show Failed, the device ID, time, policies maxRunTime and logging, and "Max run time exceeded".

## C. Compare, contrast, and scenarios

8. Contrast Decorator with **Adapter**. Both wrap. One **keeps** the interface and **adds** behaviour; the other **changes** the interface and **translates**. Which is which in this greenhouse (Phase 9 vs Phase 5)?

> [!NOTE]
> ***Your Answer***
>
> In Phase 9, Decorator keeps the ActuatorPort interface and adds logging and runtime checks.
>
> In Phase 5, Adapter translates external sensor formats into the common format used by the application. It connects different interfaces rather than adding policies around the same interface.

9. Contrast Decorator with **inheritance** of combined policies. How does composition let you add or remove a policy without a new subclass for every combination?

> [!NOTE]
> ***Your Answer***
>
> With inheritance, different policy combinations can require many subclasses. With composition, each policy is a separate wrapper. I can add or remove a wrapper when building the chain without creating another combined subclass.

10. A classmate’s decorator changes the method signature “a little” (extra required argument, different return type). Another ignores wrap order and cannot explain whether logging runs once per logical call or per inner attempt. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> Changing the method signature breaks the shared interface. Existing callers and other wrappers may no longer work with that decorator.
>
> Wrap order affects what gets logged. Logging outside retry can record one final result, while logging inside retry can record each attempt. In my chain, outer logging records one result even when the runtime check blocks execution.