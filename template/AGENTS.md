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

## Naming conventions

| Layer | Pattern | Example |
|---|---|---|
| Port | `<Noun>Repository` / `<Noun>Service` (ABC, no `I` prefix) | `UserRepository` |
| Adapter | `<Technology><Port>` | `SqlAlchemyUserRepository` |
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
