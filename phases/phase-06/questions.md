# Phase 6 — Strategy questions

**Pattern / focus:** Strategy.

**Read first:** [Guide 06](../../materials/guides/06-strategy.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example shipping quotes) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to irrigation (or lighting) policies, location context, and the automation API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Strategy in plain language. How does the **context** use a strategy, and why must “choose which algorithm” stay separate from “run the algorithm”?

> [!NOTE]
> ***Your Answer***
>
> Strategy lets me choose different algorithms through the same interface. My AutomationService chooses the saved strategy and calls decide(context). Keeping these steps separate means I can add another algorithm without changing the evaluation loop.

2. Name the participants (**strategy**, **concrete strategies**, **context**, **client**). What goes wrong when all policies live as `if/elif` inside the context (or inside an HTTP router)?

> [!NOTE]
> ***Your Answer***
>
> AutomationStrategy is the interface. ConservativeMoistureStrategy and AggressiveMoistureStrategy are the concrete strategies. AutomationService is the context that uses them. The operator chooses the strategy through the UI, which acts as the client. LocationAutomationContext holds the input data.
>
> Putting every policy in the service or router would mix the algorithms with other tasks and make the code harder to change and test.

3. When should you use Strategy, and when should you skip it (one algorithm only; or the variation is a **lifecycle mode** rather than a chosen policy)?

> [!NOTE]
> ***Your Answer***
>
> I would use Strategy when I have different ways to make the same decision. If there is only one simple algorithm, I may not need it. If behavior changes between lifecycle modes such as idle and running, State is a better choice.

## B. This phase of the application

4. In this lab, what does a strategy’s `decide(context)` return (action + reason)? Give a concrete difference you implemented (or were required to implement) between **conservative** and **aggressive** on the **same** moisture reading and zone thresholds.

> [!NOTE]
> ***Your Answer***
>
> decide(context) returns a Recommendation with an action and a reason. Conservative recommends watering below the lower threshold. Aggressive uses the midpoint of the two thresholds. With moisture 0.4 and thresholds 0.2 and 0.8, conservative returns wait and aggressive returns irrigate.

5. Where do the numbers in `LocationAutomationContext` (or your equivalent) come from? Latest moisture may already be in `sensor_readings` from a manual read, the simulation sampler, or MQTT translation — why does this phase not add a scheduler or a broker? Why must strategies receive a plain context object, not SQLAlchemy rows or FastAPI types? Why are thresholds read from **zones**, not hardcoded in the strategy class?

> [!NOTE]
> ***Your Answer***
>
> The moisture comes from the latest saved reading among moisture sensors assigned to that zone. The thresholds come from the zone settings. A zone does not use another zone's readings.
>
> Phase 5 already handles readings, so this phase only reads the stored data. It does not need another scheduler or MQTT broker.
>
> I pass a plain Python context so the strategies do not depend on SQLAlchemy or FastAPI. This makes testing easier. I use saved zone thresholds because different zones can need different settings.

6. The active `strategy_key` is **persisted** per `location_id` (for example in `automation_rules`). Why must `POST .../automation/evaluate` use the **saved** key rather than a key the client sends only in that request? What happens on the next evaluate after the operator changes strategy but moisture stays the same?

> [!NOTE]
> ***Your Answer***
>
> The saved key is the location's selected policy. Using it keeps evaluation consistent after refreshing the page or making another request.
>
> After I save a different strategy, the next evaluation uses it. With the same moisture, the result can change. For example, moisture 0.4 with thresholds 0.2 and 0.8 gives wait for conservative and irrigate for aggressive. The results will not differ for every moisture value.

7. Strategy **recommends** (irrigate / wait). It should not itself start a pump. Why keep **decide** separate from **execute**? Which later pattern is meant to carry out the action?

> [!NOTE]
> ***Your Answer***
>
> A strategy should only give advice. Otherwise, clicking Evaluate could start a pump immediately. Keeping execution separate lets me test and show recommendations without operating hardware. The later Command pattern will handle carrying out the action.

## C. Compare, contrast, and scenarios

8. Contrast Strategy with **State** (Phase 8). Both delegate to an object with the same shape. Who typically **changes** the active object, and is the variation a **policy** or a **lifecycle**?

> [!NOTE]
> ***Your Answer***
>
> Strategy changes a policy, usually chosen by the user or application. State changes behavior based on lifecycle stages, such as idle, running, or faulted. The context or state objects usually change the active state through events and transition rules.

9. Contrast Strategy with **Adapter** (Phase 5) and with **Builder** (Phase 4). Which one translates a foreign API, which one assembles a valid aggregate, and which one swaps an algorithm?

> [!NOTE]
> ***Your Answer***
>
> Adapter converts an external interface or data format, such as MQTT data into a Reading.
>
> Builder creates a valid aggregate step by step, such as a location with zones.
>
> Strategy lets me switch between algorithms, such as conservative and aggressive irrigation.

10. A classmate writes one “mega-strategy” that still contains `if conservative` / `if aggressive` inside a single class. Another strategy class calls the actuator adapter to water immediately. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> A mega-strategy still puts all algorithms in one class, so adding a policy means changing the same class again. Separate strategy classes are easier to extend and test. My registry only selects a class; it does not contain the decision logic.
>
> Starting a pump inside a strategy mixes deciding with doing. My strategy should return a recommendation, and a separate Command should handle the action.