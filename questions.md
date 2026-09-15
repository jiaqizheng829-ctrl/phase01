# Phase 1 — Skeleton Questions

## A. Patterns

1. In your own words, what is a design pattern? What is it not?

**Your answer**

A design pattern is a reusable approach to a common software design problem. It explains how parts of a program can work together. It is not a complete program or code that can be copied into every project without changes.

2. Name the three GoF pattern families. For each family, say what kind of design problem it solves. Place Factory Method and Strategy in the correct families.

**Your answer**

- Creational patterns deal with how objects are created.
- Structural patterns deal with how classes and objects are combined.
- Behavioral patterns deal with how objects communicate and share responsibilities.

Factory Method is a creational pattern. Strategy is a behavioral pattern.

3. A teammate wants to add a pattern just because it is on the course list, even though the feature is small and unlikely to grow. When should you skip a pattern? What risks come from using it too early?

**Your answer**

We should skip a pattern when a simple solution is already clear and meets the needs of the feature. Adding a pattern too early can create unnecessary classes and interfaces. This makes the code harder to understand and maintain without providing a useful benefit.

## B. This Phase of the Application

4. Why does Phase 1 deliver a vertical slice with almost no greenhouse business logic? What does “empty but running” prove that folders of unfinished classes cannot prove?

**Your answer**

Phase 1 checks that the frontend, backend, and database can work together before we add business features. An empty but running application proves that the services can start, the frontend can send requests, and the backend can connect to the database. It also lets us check the migration tools.

Empty folders alone cannot prove any of this. My project contains the basic code, but I have not yet verified the whole system because Docker failed to start on my computer.

5. List the four backend layer packages used in this course: domain, application, infrastructure, and interfaces/api. Explain what belongs in each layer and give an example of what should not belong there.

**Your answer**

- `domain` contains greenhouse business concepts and rules. For example, it could contain rules about valid sensor readings. It should not contain FastAPI routes.
- `application` contains use cases and coordinates business actions. It should not contain SQL statements for a specific database.
- `infrastructure` contains technical details such as database connections and storage implementations. It should not define the core greenhouse business rules.
- `interfaces/api` contains HTTP routes and request and response handling. It should not directly implement database storage.

My current backend uses an `app` folder. I still need to organize it into the four layer packages required by the course.

6. What does GET /health return? Why does it check the database instead of only reporting that the HTTP process has started? Why are API documents at /scalar, and why is /docs disabled?

**Your answer**

When the system is healthy, `GET /health` returns:

```json
{"status": "ok", "db": "ok"}
```

Checking the database is necessary because the API can be running while its database connection is broken. A check of the HTTP process alone would miss this problem.

The course uses `/scalar` to provide interactive API documentation based on OpenAPI. The default `/docs` page is disabled to keep one main documentation interface. Disabling `/docs` does not secure the API by itself.

My code includes `/health` and `/scalar`. It currently returns HTTP 503 when the database check fails. I still need to disable the default `/docs` page.

7. Why does Phase 1 introduce Alembic, or an equivalent tool, with a baseline migration and no business tables such as devices? What could go wrong if you create tables manually in PostgreSQL and add migrations later?

**Your answer**

The baseline checks that database migrations work before we add business tables. It gives the database a starting version so later changes can be recorded and applied in order.

If we create tables manually first, different computers may end up with different database structures. Later migrations might try to create tables that already exist or miss earlier changes.

My project has an empty baseline migration file, but I have not yet run and verified it successfully.

## C. Comparisons and Scenarios

8. Explain the dependency direction in this skeleton. Which layers can import which? Why must domain code not import FastAPI, SQLAlchemy, or Pydantic models used as HTTP schemas?

**Your answer**

Dependencies should point toward the inner business layers. The domain layer should not depend on the outer layers. The application layer can use the domain layer. The API layer calls application use cases, while infrastructure provides technical implementations of interfaces defined in the inner layers. The startup code connects these parts.

Domain code should not depend on FastAPI, SQLAlchemy, or HTTP request and response models. Otherwise, business rules become tied to a particular web framework or database. Keeping them separate makes the business rules easier to test and reuse.

9. The frontend cannot display a healthy badge, and a classmate blames “patterns.” What should you check first, including the stack, CORS or proxy settings, and health JSON? Why is this a Phase 1 issue?

**Your answer**

First, I would check that the frontend, backend, and PostgreSQL are running and that the ports and API address are correct. Then I would open `/health` directly and inspect its status code and JSON response.

If `/health` works directly but the frontend request fails, I would check the browser console and network requests for CORS or proxy problems. I would also check that the frontend reads the correct `status` and `db` fields.

These are basic connection and configuration issues. Phase 1 must solve them before later business features and design patterns are added.

10. The course finishes at Phase 12, not Phase 1. What is still missing after a successful skeleton? How can later phases add behavior without rewriting the foundation?

**Your answer**

The skeleton still needs real greenhouse features, such as device and sensor management, configuration, automation, controls, and events. These features also need database tables, API endpoints, user interface elements, and tests.

Later phases can add business rules to the domain layer, use cases to the application layer, and technical implementations to infrastructure. The API layer exposes the new actions, and migrations update the database. The frontend replaces placeholder areas with working features.

This allows us to reuse the existing startup setup, database connection, API documentation, and frontend foundation.



# Phase 2 — Factory Method Questions

## A. Pattern

### 1. State the intent of Factory Method in plain language. What problem appears when callers scatter `new` constructors (or a growing `if type == ...`) across the application?

**Your Answer**

Factory Method separates the decision of which object to create from the code that uses the object. Without it, API handlers and services can become full of repeated constructors or `if type == ...` branches. It is not a complete application architecture or a reason to create many classes for a very small feature.

### 2. Name the main participants of Factory Method (**product**, **concrete product**, **creator**, **concrete creator**, **client**). For each, give one sentence: what it is responsible for.

**Your Answer**

The product is the common object created by the pattern; here it is a sensor device. A concrete product is one specific result, such as a moisture or light sensor. The creator defines the creation operation. A concrete creator supplies the defaults for one sensor type. The client asks a creator for a product without depending on a concrete sensor class.

### 3. How do you add a **new product variant** when creators are polymorphic (new class + registry entry) versus when creation lives in one shared `if/elif` function? Why does that difference matter for extension?

**Your Answer**

With polymorphic creators, I add a new creator class and register its key. With one shared `if/elif` factory, I must edit the central function every time. The registry approach keeps the creation rules close to each sensor type and makes extension more local.

## B. This phase of the application

### 4. In this lab, what is the **product** and what are the **concrete creators**? Why must the API handler (or sensor service) go through a creator/registry instead of constructing `MoistureSensor` or `LightSensor` itself?

**Your Answer**

The product is the `Sensor` domain object. The concrete creators are `MoistureSensorCreator` and `LightSensorCreator`. The API handler should use the registry and service so it does not need to know how a specific sensor is constructed or which defaults it needs.

### 5. `POST /api/sensors` accepts a short key such as `type: "moisture"` or `type: "light"`, while the stored/returned field is `device_type` (for example `moisture_sensor`). Why are those two fields different? Who decides the stored `device_type` and `default_config`?

**Your Answer**

The short `type` field is an input key chosen for a simple client API, such as `moisture` or `light`. The stored `device_type` is the more specific internal device identity, such as `moisture_sensor`. The selected creator decides both the stored device type and the default configuration.

### 6. Why is there a single `devices` table with `role="sensor"` instead of a dedicated `sensors` table? What later phase does that choice prepare for?

**Your Answer**

A single `devices` table keeps shared device data in one place, while `role="sensor"` identifies sensor rows. This prepares the project for a later phase where actuators can use the same table without rebuilding the database design.

### 7. What should happen when the client posts an **unknown** `type`? Where should that rejection be decided (registry/service vs router constructing a concrete class anyway)?

**Your Answer**

An unknown type should be rejected with a clear client error, such as HTTP 400. The registry or application service should make this decision because it owns the supported creation options. The router should not construct a concrete class as a fallback.

## C. Compare, contrast, and scenarios

### 8. Contrast Factory Method with a **simple factory** (one function full of `if type == ...`). When is the simple factory “good enough,” and why does this phase still want polymorphic creators?

**Your Answer**

A simple factory is one function with `if type == ...` branches. It is good enough when there are only a few stable variants and the feature is unlikely to grow. This phase uses polymorphic creators because moisture and light have different defaults, and later sensor variants can be added through another creator and registry entry.

### 9. Contrast Factory Method with **Abstract Factory** (Phase 3). Factory Method answers which question? Abstract Factory answers which different question? Why is Factory Method enough for Phase 2 sensors?

**Your Answer**

Factory Method answers: “Which concrete sensor should create this product?” Abstract Factory answers: “Which related family of products should be created together?” Factory Method is enough in Phase 2 because the application only needs to choose one sensor type at a time. Phase 3 can use Abstract Factory for related device families.

### 10. A classmate puts SQLAlchemy session commits (or FastAPI request parsing) **inside** a concrete creator. Why is that a trap? Where should persistence and HTTP stay instead?

**Your Answer**

A concrete creator should only create a domain sensor with the correct defaults. Putting database commits inside it mixes creation rules with persistence, and FastAPI parsing mixes it with HTTP details. Persistence belongs in the repository or infrastructure layer, while request parsing and HTTP responses belong in the API layer.
