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
