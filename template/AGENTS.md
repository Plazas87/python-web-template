# AGENTS.md — {{ project_name }}

Read this before writing, modifying, or suggesting code. It describes where code belongs,
what is forbidden, and how the architecture is enforced. `import-linter` (see
"Enforcement" below) is authoritative when this document and the code disagree.

## Architecture overview

Ports & Adapters (Hexagonal Architecture). Dependencies point inward only. Adapters depend
on ports; application depends on domain; domain depends on nothing outside itself. This is
the Dependency Inversion Principle applied architecturally — reference:
[Herberto Graca, "Explicit Architecture"](https://herbertograca.com/2017/11/16/explicit-architecture-01-ddd-hexagonal-onion-clean-cqrs-how-i-put-it-all-together/).

## The three zones

| Zone | Allowed imports | Contains |
|---|---|---|
| `domain/` | Nothing outside `domain/` | Entities, value objects, domain services, domain events, port interfaces (ABCs) |
| `application/` | `domain/` only | Use cases — one class per business action, one public method: `execute` |
| `adapters/` | `domain/` ports and external libraries | HTTP routers, database repositories, external API clients, observability setup |

Ports live in `domain/ports/`, never in `adapters/`. The concrete adapter implements the
ABC; the application layer imports only the ABC.

## SOLID rules as patterns

- **S** — one use case per business action, one file each.
- **O** — new integrations are new adapter classes; existing ports are not modified to fit a new adapter.
- **L** — every adapter implementing a port must be substitutable for any other implementation of that port.
- **I** — port interfaces stay small and focused, not god-interfaces.
- **D** — domain and application depend on ABCs only, never on concrete adapter classes. Concrete classes are wired together in exactly one place: `container.py`.

## Decision tree — where does new code go?

- **New business rule** → `domain/model/` (entity/value object) or `domain/services/` (cross-entity logic).
- **New HTTP endpoint** → `adapters/inbound/http/router.py` (or a new router module), calling an existing or new use case in `application/use_cases/`.
- **New database table** → `adapters/outbound/persistence/models.py` (SQLAlchemy model) + an Alembic migration. Never let the SQLAlchemy model leak into `domain/model/`.
- **New third-party integration** (email, payments, etc.) → define the port in `domain/ports/services.py` if one doesn't exist, implement it in `adapters/outbound/external/`, wire it in `container.py`.
- **New authorization rule** ("can this actor do this?") → a check inside the relevant use case via the `Policy` port (`domain/ports/policy.py`), never only as a FastAPI dependency. See "Authentication vs. authorization" below.
- **Something that runs outside the request/response cycle** (on a schedule, or some time after X) → a job function in `adapters/inbound/scheduler/jobs.py`, registered with the `AsyncIOScheduler` in `main.py`'s `lifespan`. See "Background jobs" below.
- **A new domain event, or something that should react to one** → define the event in `domain/events.py` (past tense, frozen dataclass), `dispatch()` it from the use case via the `EventDispatcher` port right after the state change it describes, and add a subscriber in `container.py`'s `_event_dispatcher`. See "Domain events" below.
- **A new "list X" endpoint** → `domain/model/pagination.py`'s `PageRequest`/`Page` on the repository port (a `list_page(page_request) -> Page[T]` method), not a bespoke offset/limit convention per entity. See `UserRepository.list_page` and `GET /users` for the pattern.
- **A new low-complexity entity** (no state machine, no validation beyond "field is required," nothing that would ever need independent persistence) → a candidate for a generic, parameterized CRUD port/adapter instead of full per-entity ceremony. See "Generic-CRUD escape hatch" below before reaching for a bespoke `<Entity>Repository`.

## Authentication vs. authorization

These are different concerns, enforced in different layers:

- **Authentication** ("is there a valid session at all?") is an HTTP-layer guard:
  `get_current_user` (`adapters/inbound/http/dependencies.py`) decodes the bearer token and
  loads the actor, or 401s. It has no opinion on what that actor may do.
- **Authorization** ("is *this* actor allowed to do *this*?") is a business rule and belongs
  *inside* the use case, via `Policy.can(actor, action, resource)` (`domain/ports/policy.py`,
  implemented by `RoleBasedPolicy`) — see `ListUsersUseCase` for the pattern. A rule enforced
  only as a route dependency can be silently bypassed by any non-HTTP caller (a background
  job, a script, another adapter); a rule enforced inside the use case can't be.

## Background jobs

Staged the same way observability is staged (day one → first paying user → stable
revenue) — apply the same reasoning here instead of reaching for a queue on day one:

- **Default / starting point**: in-process `AsyncIOScheduler` (APScheduler), started and
  shut down in `main.py`'s `lifespan`. Zero extra infrastructure; fine for a single service
  at modest scale. See `log_user_count_heartbeat` (`adapters/inbound/scheduler/jobs.py`)
  for the pattern — a job has no FastAPI request to hang `Depends(get_db_session)` off, so
  it opens and closes its own session directly from the `Container` it's given, the same
  way `scripts/seed.py` does.
- **Graduate to this when the pain shows up**: Celery or RQ + Redis, once there's real
  queueing/retry/distributed-worker need.

## Domain events

`domain/events.py` declares events (e.g. `UserCreated`); a use case dispatches one via the
`EventDispatcher` port (`domain/ports/events.py`) right after the state change it describes,
in the *same* session/transaction — see `RegisterUserUseCase` for the pattern. `InProcessEventDispatcher` (`adapters/outbound/events/`) is the default: it calls
subscribed handlers synchronously, in-process. `AuditLogConsumer`
(`adapters/outbound/persistence/audit_log_consumer.py`) is the first subscriber — a generic
sink that records event name, payload, and timestamp for *any* dataclass event, giving every
generated project a working audit trail for free. Subscriptions are wired in `container.py`'s
`_event_dispatcher`, once, per request.

## Generic-CRUD escape hatch

The default in this document — domain model + port + adapter + one use case per verb, per
entity — is the right ceremony for entities with real business rules. It's needless
boilerplate for simple lookup/reference tables (a list of tags, a country list, an audit
category) that are functionally just insert/update/soft-delete/list, with nothing to
protect.

Ask this before writing the full ceremony for a new entity: does it have a state machine, a
validation rule beyond "field is required," or a reason someone would ever swap its
persistence independently? If the answer to all three is no, it's a candidate for a generic
path instead — one parameterized `CrudRepository[ModelT]` port + SQLAlchemy adapter, reused
across every such entity, rather than a bespoke `<Entity>Repository` /
`SqlAlchemy<Entity>Repository` pair each time. This template doesn't ship one by default
(nothing in it qualifies yet), but treat a generic CRUD port as the sanctioned way to
deviate for entities like this — not a violation of the architecture, and not a reason to
silently skip the ports-and-adapters pattern altogether either.

## Naming conventions

| Layer | Pattern | Example |
|---|---|---|
| Port | `<Noun>Repository` / `<Noun>Service` (ABC, no `I` prefix) | `UserRepository` |
| Adapter | `<Technology><Port>` | `SqlAlchemyUserRepository` |
| Policy adapter | `<Strategy>Policy` | `RoleBasedPolicy` |
| Use case | `<Verb><Noun>UseCase` | `CreateUserUseCase` |
| Domain event | Past tense | `UserCreated` |

## Anti-patterns — do not do this

- Business logic in HTTP routers (routers validate, call a use case, return a response — nothing else).
- SQLAlchemy, FastAPI, or any adapter-layer import inside `domain/`.
- A use case importing a concrete adapter class instead of a port ABC.
- A use case class with more than one public method — split it into two use cases.
- Wiring concrete adapters anywhere other than `container.py`.
- A `yield`-style FastAPI dependency (`Depends(...)` with a `yield`) written as a sync
  generator — always `async def` with `async for`/`yield` instead, even if the body is
  synchronous. See `container.py`'s `new_session` for why and the shape to copy.

## Composition root

`container.py` is a plain `Container` dataclass with a `build()` classmethod — a manual
factory, not a DI framework. It is the only file where concrete adapter class names and
use case class names appear together. Everything else depends on port ABCs, injected via
FastAPI's `Depends()` in `adapters/inbound/http/router.py`.

## Testing rules

- `tests/unit/` — no I/O. Inject fake/in-memory implementations of port ABCs (see
  `tests/unit/application/test_create_user.py` for the pattern). Must run without a database.
- `tests/integration/` — exercises adapters against a real database via `TestClient`.

## Observability rules

| Layer | What to log | Level |
|---|---|---|
| HTTP middleware | Request in, response out, latency, status code | INFO |
| Use cases | Started, completed, failed with reason | INFO / ERROR |
| Domain events | Event name, aggregate ID | INFO (audit trail) |
| Outbound adapters | Queries and external calls | DEBUG (never INFO in production) |

Never log passwords, raw tokens, or unmasked PII. `trace_id` is bound once per request by
`TracingMiddleware` via a `ContextVar` (`adapters/outbound/observability/logging.py`); every
log line and OTEL span in that request shares it. `/health` checks the process only
(no dependencies, must be fast); `/ready` checks the database and returns 503 if unreachable.

## Enforcement

`import-linter` contracts (`pyproject.toml`) run in CI (`make architecture`) and
pre-commit. A dependency-rule violation fails the build before a human reviews the code —
this document describes the architecture, `import-linter` is what makes it real.
