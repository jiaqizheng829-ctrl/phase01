# Phase 10 — Command questions

**Pattern / focus:** Command.

**Read first:** [Guide 10](../../materials/guides/10-command.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example editor undo commands) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to command objects, the invoker, `command_log`, and the controls UI from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Command in plain language. What does it mean to **objectify a request**, and what can you do with that object that you cannot do with a bare `actuator.start()` call (queue, audit, undo, history)?

> [!NOTE]
> **_Your Answer_**
>
> Command represents a request as an object containing the action, target device, and payload. The request can be passed around and executed separately from its creation. This makes it easier to add queues, auditing, history, or undo support than with an immediate method call alone. My implementation executes commands synchronously and records history; it does not implement a queue or undo.

2. Name the participants (**command**, **receiver**, **invoker**, **client**). Who creates the command, who triggers `execute()`, and who actually changes actuator/hardware state?

> [!NOTE]
> **_Your Answer_**
>
> The concrete commands are StartPumpCommand, StopPumpCommand, and SetLightLevelCommand. The receiver is the actuator port supplied to execute(), which wraps the simulation adapter with decorators. CommandInvoker creates commands through the registry and triggers execute(). CommandService acts as the client that coordinates command creation and supplies the decorated receiver. The adapter represents the actuator operation, while CommandService separately validates and saves database state changes through ActuatorContext. Physical hardware is not controlled in this implementation.

3. If a command supports undo, when must it capture the data needed to reverse the action? Why is “capture **before** mutate” critical?

> [!NOTE]
> **_Your Answer_**
>
> It must capture the previous values before changing them. For example, undoing a light-level change would require the previous light level. Capturing it afterward would only provide the new value, so the original state could not be restored reliably. Hardware actions may also need a compensating action rather than a perfect reversal. Undo is not implemented in this phase.

## B. This phase of the application

4. Which command types did you implement (for example `start_pump`, `stop_pump`, `set_light_level`)? Why does the HTTP handler create a command and pass it to an **invoker** (or application service) instead of calling the actuator adapter from the router?

> [!NOTE]
> **_Your Answer_**
>
> I implemented start_pump, stop_pump, and set_light_level. The HTTP handler passes the request to CommandService, which uses CommandInvoker and the command registry. This keeps HTTP handling separate from state validation, decorated execution, and persistence. Calling the adapter directly from the router could bypass these checks and omit command history.

5. Walk through the execute path: (1) consult State / `allowed_commands`, (2) if illegal → **rejected**, (3) if legal → decorated `apply`, update `actuator_states`, log **success** or **failed**. Why must a rejected command **not** change actuator state and **not** reach inner `apply`?

> [!NOTE]
> **_Your Answer_**
>
> The service validates the actuator, locks its saved state, and creates the command through the invoker. It checks the command type against ActuatorContext.allowed_commands(). An illegal command is logged as rejected and execution stops. Otherwise, the invoker executes the command through LoggingDecorator and MaxRunTimeDecorator. An execution error produces a failed command log without changing actuator state. After successful execution, the service transitions and saves the state only when the target differs, then records success. A rejected command must not reach the adapter or change state because that would perform an action that the state rules explicitly forbid.

6. Distinguish **`rejected`** vs **`failed`** vs **`success`** in `command_log`. Give one greenhouse example of each. Why is “illegal in this state” not the same as “policy or adapter error after the command was accepted”?

> [!NOTE]
> **_Your Answer_**
>
> Rejected means the command is not permitted for the saved state, such as starting an already running pump. Failed means the command passed the state check but execution did not complete, such as stopping a pump that the current runtime decorator blocks after 30 minutes. Success means execution completed, such as starting an idle pump and saving its running state. State rejection happens before decorated execution; a policy or adapter failure happens after the command has passed that first check.

7. Why is `command_log` a **different** table from Phase 9 `actuator_execution_log`? What concern does each log record (operator intent vs policy/adapter attempt)?

> [!NOTE]
> **_Your Answer_**
>
> command_log records the requested action, device, payload, and overall outcome, including rejected requests. actuator_execution_log records attempts through the decorated port, including applied policies and execution errors. A state-rejected command has a command log but no execution log because it never reaches the port. A runtime-blocked command has both logs. Keeping them separate distinguishes the operator's request from the execution policies applied to it.

## C. Compare, contrast, and scenarios

8. Contrast Command with **Strategy**. Strategy is an interchangeable **algorithm** (decide / quote). Command is a **side-effectful request** with history. How do they cooperate in this app (Phase 6 recommends; Phase 10 executes)?

> [!NOTE]
> **_Your Answer_**
>
> Strategy selects an interchangeable decision-making algorithm. In Phase 6, conservative and aggressive strategies produce recommendations from readings and thresholds. Command represents an action to execute, such as starting a pump, with state checks and recorded results. A recommendation can inform a later command, but my application does not automatically execute recommendations: the operator submits commands through the controls UI.

9. Contrast Command with **State**. Who **triggers** the action, and who **decides whether it is legal**? Why must commands not bypass state guards?

> [!NOTE]
> **_Your Answer_**
>
> The operator requests an action, and the invoker triggers the command's execute() method. State determines whether that action is legal in the actuator's current condition. CommandService checks these permissions before execution and uses ActuatorContext.transition for state changes. Bypassing the guards could allow invalid operations, such as starting a pump that is already running or executing commands during maintenance.

10. The controls UI should disable actions that are not in `allowed_commands`. Why must the **backend** still reject illegal commands even if the UI is correct? What happens if a classmate’s command calls the raw adapter and skips State and Decorator?

> [!NOTE]
> **_Your Answer_**
>
> Requests can come from scripts or other clients, and the device state may change after the UI loads. Disabled buttons therefore cannot replace backend validation. The backend checks the saved state while holding a lock. Calling the raw adapter would bypass state permissions, the runtime limit, and execution logging. The action could then run when it should be blocked, and the audit history could be incomplete.