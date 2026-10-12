# Strategy Pattern — Phase 6

## Problem

Different locations may need different irrigation policies. Putting every policy inside an API handler would mix HTTP handling, database access, and decision logic.

The Strategy pattern puts interchangeable algorithms behind a common interface. The application selects an algorithm using the strategy key saved for a location.

## Interface and participants

The domain interface is:

```python
class AutomationStrategy(ABC):
    @abstractmethod
    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        raise NotImplementedError
```

- `AutomationStrategy` defines the common decision interface.
- `ConservativeMoistureStrategy` and `AggressiveMoistureStrategy` implement different policies.
- `LocationAutomationContext` is a plain Python dataclass containing location and zone IDs, zone thresholds, latest moisture, and whether a moisture sensor is assigned.
- `Recommendation` contains an action (`irrigate` or `wait`) and a reason.
- `AutomationService` selects the saved strategy and calls it once for each zone.
- `get_strategy()` resolves known keys and rejects unknown keys before a decision is made.

The domain does not import SQLAlchemy, FastAPI, or Pydantic.

## Algorithms

Conservative recommends irrigation when:

```text
latest_moisture < moisture_threshold_low
```

Aggressive recommends irrigation when:

```text
latest_moisture < (moisture_threshold_low + moisture_threshold_high) / 2
```

Equality with the strategy's threshold produces `wait`.

For the same context:

| Low | High | Moisture | Conservative | Aggressive |
|---|---|---|---|---|
| 0.2 | 0.8 | 0.4 | wait | irrigate |

The strategies differ when moisture is at or above the lower threshold but below the midpoint. Both use the zone's stored thresholds rather than hardcoded moisture limits.

## Persistence

The implementation uses a dedicated `automation_rules` table:

- UUID primary key
- Unique `location_id` foreign key referencing `locations`
- `strategy_key`
- JSONB `parameters`, currently unused and defaulting to an empty object
- Timezone-aware `updated_at`

The unique constraint allows one saved strategy per location. Saving again updates the existing row. Deleting a location cascades to its automation rule.

Migration `9d391b40fb2f` adds this table after Phase 5 migration `3b45041792c3`.

A location without a saved rule reports `strategy_key: null`. Evaluation returns HTTP 400 until a strategy is saved. No default strategy is silently persisted.

## Building the context

`AutomationContextRepository` loads every zone in the requested location.

For each zone, it:

1. Reads the zone's lower and upper moisture thresholds.
2. Finds moisture sensors assigned through `devices.zone_id`.
3. Selects the newest stored reading among those sensors, ordered by reading time and then reading ID.
4. Converts database values into a plain `LocationAutomationContext`.

Readings from unassigned sensors, other zones, other locations, and light sensors are excluded.

The query does not filter by reading source. Persisted readings from manual reads, simulation sampling, or translated MQTT payloads can be used.

If no moisture sensor is assigned, the strategy returns `wait` with an explanatory reason. If a sensor exists but has no stored reading, it also returns `wait` with a distinct reason.

This phase uses the latest stored reading without an age limit. A future stale-reading policy would need an explicit requirement and tests.

## Application and API

The application validates the location, loads the persisted key, selects the strategy, builds zone contexts, and maps recommendations into response DTOs.

Endpoints:

- `GET /api/locations/{location_id}/automation`
- `PUT /api/locations/{location_id}/automation`
- `POST /api/locations/{location_id}/automation/evaluate`

Save request:

```json
{
  "strategy_key": "conservative"
}
```

Unknown strategy keys return HTTP 400. Missing locations return HTTP 404.

Evaluation accepts no strategy override: it uses the key saved in the database.

The evaluation response contains `location_id`, `strategy_key`, an overall `action` and `reason`, and a `zones` list with individual results. The overall action is `irrigate` if at least one zone recommends irrigation; otherwise it is `wait`. A location without zones returns `wait` and an empty list.

These endpoints are registered with FastAPI and included in its OpenAPI schema.

## Dashboard

`StrategyPanel` is mounted in the Dashboard's `#automation` section.

Users can select a location, load its saved strategy, save a different strategy, and evaluate the latest stored readings. The panel displays each zone's moisture, thresholds, action, and reason.

Evaluation is disabled until a strategy is saved and when the dropdown contains an unsaved change. Success and error messages explain the result of requests.

Evaluation results are displayed in the current page state; they are not persisted as recommendation history.

## Decide versus execute

A recommendation does not operate a pump.

Strategies perform no database writes, network calls, or actuator commands. Evaluation does not generate new sensor readings. A later Command implementation can handle execution separately.

## Code locations

Paths below are relative to the repository root.

- `backend/app/domain/automation/context.py`
- `backend/app/domain/automation/strategy.py`
- `backend/app/application/automation/dto.py`
- `backend/app/application/automation/service.py`
- `backend/app/infrastructure/automation_repository.py`
- `backend/app/infrastructure/automation_context_repository.py`
- `backend/app/interfaces/api/automation.py`
- `frontend/src/api/automation.ts`
- `frontend/src/components/automation/StrategyPanel.tsx`

## Verification

- 23 strategy unit tests passed.
- 6 automation API integration tests passed.
- The complete backend suite passed: 97 tests, with one dependency deprecation warning.
- Frontend TypeScript checking and production build passed.
- Manual API checks demonstrated different recommendations for the same stored moisture value after changing the saved strategy.
- Dashboard checks demonstrated loading saved settings and displaying evaluation results.

Integration tests verify persistence, a single rule per location, unknown-key rejection, missing locations, unconfigured locations, empty locations, and isolation of zone readings.

Tests use a separate database and roll back their temporary data.

## Exercise: add a third strategy

Add a `BalancedMoistureStrategy` that recommends irrigation below:

```text
low + (high - low) / 3
```

To implement it:

1. Implement `AutomationStrategy.decide()` in a new concrete class.
2. Reuse the missing-sensor and missing-reading behavior.
3. Register the `balanced` key in the strategy registry.
4. Extend the frontend strategy-key type and dropdown.
5. Add boundary tests and an API test for the new key.
6. Document how its recommendations differ from the existing strategies.

The API handlers and evaluation loop should not need algorithm-specific branches.