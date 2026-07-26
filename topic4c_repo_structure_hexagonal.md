# Repo Structure — Python Web Application (Hexagonal Architecture)
### Topic 4c of 10 — Pipeline Series

---

## What this document covers

Topic 4 defined a baseline repo structure for Python web applications. This document supersedes that baseline with an explicit, enforced architecture: Ports & Adapters, also known as Hexagonal Architecture.

The additions are not cosmetic. They represent decisions that affect every file written from day one: a formal separation between domain logic and infrastructure, a composition root that makes dependency inversion real, and an observability layer with clear boundaries.

Two practices that often appear alongside hexagonal architecture are deliberately excluded: **CQRS** and a **distributed shared kernel**. Both are valuable at scale. Neither is appropriate before you have paying users and a codebase large enough to feel the pain they solve. Structure follows pain, not anticipation of it.

An **AI agent coordination layer** was considered for this structure and removed. If and when agent orchestration becomes part of this project, it deserves its own dedicated planning pass rather than being bolted onto the web application structure prematurely.

> **Prerequisite:** read Topic 4 (web application baseline) and Topic 2 (what to cut) before this document. The dependency rule in hexagonal architecture supersedes any structural convention from earlier topics.

> **Assumption flagged for confirmation:** this revision uses Python's standard library `logging` module combined with `contextvars` for structured logging, instead of `structlog`. This keeps the observability layer at zero additional dependencies and integrates natively with how FastAPI, SQLAlchemy, and Alembic already log. `structlog`'s composable processor pipeline is a legitimate alternative if that ergonomic pattern is preferred over the dependency saving — see Section 7 for the full tradeoff.

---

## 1. The full structure

Every folder exists for one reason. Nothing in the tree below is aspirational — everything has an immediate purpose tied to a pipeline layer.

```text
your-project/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # Lint, typecheck, arch check, tests on every push
│   │   └── release.yml             # Tag-triggered release job
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
│
├── src/
│   └── your_app/
│       │
│       ├── domain/                 # Innermost ring — zero external dependencies
│       │   ├── model/              # Entities and Value Objects
│       │   │   └── user.py
│       │   ├── ports/              # Port interfaces as Python ABCs
│       │   │   ├── repositories.py # UserRepository, OrderRepository (ABCs)
│       │   │   └── services.py     # EmailService, PaymentService (ABCs)
│       │   ├── services/           # Domain services (cross-entity logic)
│       │   └── events.py           # Domain events (past-tense, named)
│       │
│       ├── application/            # Use cases — knows domain, blind to infra
│       │   └── use_cases/          # One file per business action
│       │       └── create_user.py
│       │
│       ├── adapters/
│       │   ├── inbound/            # Primary: tell the app to do something
│       │   │   └── http/
│       │   │       ├── middleware/
│       │   │       │   ├── tracing.py   # Bind trace_id via ContextVar per request
│       │   │       │   ├── logging.py   # Structured request/response logs
│       │   │       │   └── metrics.py   # Latency, status codes, request count
│       │   │       ├── health.py        # /health and /ready endpoints
│       │   │       ├── router.py        # FastAPI route handlers
│       │   │       └── schemas.py       # Request/Response DTOs (Pydantic)
│       │   │
│       │   └── outbound/           # Secondary: told by the app to do something
│       │       ├── persistence/
│       │       │   ├── models.py        # SQLAlchemy ORM models (not domain models)
│       │       │   ├── migrations/      # Alembic migrations
│       │       │   └── repositories.py  # SqlAlchemyUserRepository (implements ABC)
│       │       ├── external/            # Third-party API clients
│       │       │   └── stripe.py        # Implements PaymentService ABC
│       │       └── observability/
│       │           ├── logging.py       # stdlib logging + ContextVar configuration
│       │           ├── metrics.py       # Prometheus / OTEL metrics setup
│       │           └── tracing.py       # OpenTelemetry SDK configuration
│       │
│       ├── container.py            # Composition root — wires ports to adapters
│       └── config.py               # Single os.environ reader
│
├── tests/
│   ├── unit/                       # Domain + application — no I/O
│   └── integration/                # Adapters with real DB and network
│
├── docker/
│   ├── Dockerfile                       # Multi-stage: builder + slim runtime
│   ├── docker-compose.yml               # App + DB for local development
│   └── docker-compose.observability.yml # Prometheus + Grafana + Jaeger (future state)
│
├── scripts/
│   ├── seed.py
│   ├── migrate.py
│   └── reset_db.py
│
├── AGENTS.md                       # Project brain for AI coding agents (Claude Code, etc.)
├── .env.example
├── .env
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── uv.lock                         # Committed — exact reproducible installs
├── Makefile
└── README.md
```

> **Note on `AGENTS.md`:** this file is unrelated to the AI agent orchestration layer that was removed from `src/`. It is a context document read by AI coding assistants (Claude Code, Cursor, and similar tools) so they understand this project's architecture before generating code. It stays regardless of whether the application itself ever has agent features.

---

## 2. Architecture: Ports & Adapters

Every decision in this structure follows one rule. It has no exceptions.

> **Dependencies point inward only.** Adapters depend on ports. Application depends on domain. Domain depends on nothing outside itself.

This rule — the Dependency Inversion Principle applied at the architectural level — is what makes the rest of the structure coherent. When it is followed consistently, you can swap any outbound adapter without touching domain or application code. When it is violated, the architecture is cosmetically hexagonal and practically none of it.

### The three zones

| Zone | Allowed imports | Contains |
|---|---|---|
| `domain/` | Nothing outside `domain/` | Entities, Value Objects, domain services, domain events, port interfaces (ABCs) |
| `application/` | `domain/` only | Use cases — one class per business action, nothing else |
| `adapters/` | `domain/` ports and external libraries | HTTP routers, database repositories, external API clients, observability setup |

### Ports belong in `domain/`, not in `adapters/`

The most common mistake in hexagonal Python codebases is placing port interfaces next to their implementations in the adapter layer. This reverses the dependency: the application layer then imports from the adapter layer to get the interface it needs, which is precisely what the architecture is designed to prevent.

Ports belong in `domain/ports/`. They are owned by the application core, defined by what the core needs, and never shaped by what the infrastructure happens to provide. The concrete adapter implements the ABC. The application layer imports the ABC. The adapter layer is never imported by anything inside the core.

### Python naming convention for ports

Port interfaces in Python are abstract base classes. They follow the same naming convention as Python's standard library — no `I` prefix. The abstract class is the port. Concrete implementations carry the distinguishing prefix.

```python
# domain/ports/repositories.py
from abc import ABC, abstractmethod

class UserRepository(ABC):                 # the port
    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def find_by_id(self, id: UserId) -> User | None: ...


# adapters/outbound/persistence/repositories.py
class SqlAlchemyUserRepository(UserRepository):   # the adapter
    def save(self, user: User) -> None:
        ...  # SQLAlchemy implementation

    def find_by_id(self, id: UserId) -> User | None:
        ...  # SQLAlchemy implementation
```

---

## 3. `domain/` — the innermost ring

The domain layer contains the business rules that are true regardless of how the application is delivered, what database it uses, or what external services it calls. It is the most important code in the project and the most protected. It imports nothing from outside itself.

### `domain/model/` — entities and value objects

Entities are objects with identity — an ID that persists across time and state changes. Value objects are immutable descriptors with no identity of their own. Both are plain Python classes with no framework imports. Business rules are enforced here, in the model, not in the use case.

```python
# domain/model/user.py
from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    name: str = ""

    @classmethod
    def create(cls, email: str, name: str) -> "User":
        if not email or "@" not in email:
            raise ValueError(f"Invalid email: {email}")
        return cls(email=email.lower().strip(), name=name.strip())
```

### `domain/ports/` — what the core needs from the outside world

Port interfaces express the core's needs in domain language, not infrastructure language. A repository port looks like a collection of domain objects, not a database query interface. A payment port looks like a business operation, not a payment gateway API. The concrete implementations are someone else's problem.

### `domain/events.py` — things that happened

Domain events record significant state changes in the domain. They are named in the past tense (`UserCreated`, `OrderCancelled`), carry the data that changed, and are raised by entities or domain services. The application layer consumes them to trigger side effects — sending an email, logging an audit entry.

---

## 4. `application/` — use cases

The application layer contains one thing: use cases. A use case is a single business action — `CreateUser`, `ProcessPayment`, `CancelOrder`. It orchestrates domain objects and calls domain ports. It knows the domain. It does not know FastAPI, SQLAlchemy, or any other infrastructure. CQRS — separate command objects, command buses, query handlers — is excluded until the complexity of read and write models makes it genuinely necessary.

### One class per use case — Single Responsibility made structural

Each use case lives in its own file. The class has one public method: `execute`. If a use case class grows a second public method that handles a different business action, it is two use cases and should be split into two files.

```python
# application/use_cases/create_user.py
import logging
from your_app.domain.model.user import User
from your_app.domain.ports.repositories import UserRepository
from your_app.domain.ports.services import EmailService

log = logging.getLogger(__name__)

class CreateUserUseCase:
    def __init__(self, repo: UserRepository, email_svc: EmailService):
        # Receives ABCs. Never sees SqlAlchemyUserRepository.
        self._repo = repo
        self._email = email_svc

    def execute(self, email: str, name: str) -> User:
        log.info("use_case.started", extra={"context": {"action": "create_user"}})
        user = User.create(email, name)       # domain enforces the rule
        self._repo.save(user)
        self._email.send_welcome(user)
        log.info("use_case.completed", extra={"context": {"user_id": str(user.id)}})
        return user
```

> The use case imports `UserRepository` and `EmailService` — the ABCs from `domain/ports/`. It never imports `SqlAlchemyUserRepository` or a concrete email adapter. Concrete implementations are injected at startup by `container.py`. This is Dependency Inversion made structural, not just philosophical.

---

## 5. `adapters/` — the outer ring

Adapters translate between the application core and the outside world. Inbound adapters (primary) receive external input and call use cases. Outbound adapters (secondary) implement domain ports using real infrastructure. Neither side knows about the other.

### `adapters/inbound/http/` — FastAPI routes

HTTP route handlers are the only code that knows about FastAPI. A route handler does three things and nothing else: validates the incoming request using Pydantic schemas, calls a use case, and returns a response. No business logic lives here.

```python
# adapters/inbound/http/router.py
from fastapi import APIRouter, Depends
from your_app.adapters.inbound.http.schemas import CreateUserRequest, UserResponse
from your_app.application.use_cases.create_user import CreateUserUseCase
from your_app.container import Container

router = APIRouter()

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUserUseCase = Depends(Container.create_user),
) -> UserResponse:
    user = use_case.execute(request.email, request.name)
    return UserResponse.from_domain(user)
```

### `adapters/inbound/http/middleware/` — observability at the HTTP boundary

HTTP middleware is where observability begins. Every request gets a trace ID bound to a `ContextVar`, its arrival and departure logged, and its latency recorded. This happens once, at the boundary, without touching any use case or domain code.

| Middleware file | What it does | Effect |
|---|---|---|
| `tracing.py` | Extracts or generates a trace ID from the request header, sets it on a `ContextVar` for the request's async task | Every log entry in the request carries the same `trace_id` automatically |
| `logging.py` | Logs request method, path, status code, and duration as a single structured JSON entry | One log line per request with all context needed to debug any issue |
| `metrics.py` | Increments request counter and records latency histogram keyed by route and status code | Feeds the `/metrics` endpoint scraped by Prometheus or OTEL Collector |

### `adapters/inbound/http/health.py` — two endpoints, two contracts

| Endpoint | Contract | Checked by |
|---|---|---|
| `/health` | Returns 200 if the process started correctly. No dependencies checked. Must always be fast. | Docker / Kubernetes liveness probe — every 10s |
| `/ready` | Returns 200 only when DB is reachable and required services are available. Returns 503 otherwise. | Load balancer — stops routing traffic until 200 is returned |

### `adapters/outbound/` — implementations of domain ports

Outbound adapters implement the ABCs defined in `domain/ports/`. The application core calls the ABC. The adapter does the real work. Swapping a database means writing a new class that implements the same ABC. Nothing in `domain/` or `application/` changes.

```python
# adapters/outbound/persistence/repositories.py
from sqlalchemy.orm import Session
from your_app.domain.model.user import User
from your_app.domain.ports.repositories import UserRepository
from your_app.adapters.outbound.persistence.models import UserModel

class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session):
        self._session = session

    def save(self, user: User) -> None:
        model = UserModel.from_domain(user)
        self._session.merge(model)
        self._session.flush()

    def find_by_id(self, id) -> User | None:
        model = self._session.get(UserModel, id)
        return model.to_domain() if model else None
```

---

## 6. Observability

Observability is an outbound concern. The application pushes logs, metrics, and traces to external systems the same way it pushes data to a database. HTTP-level observability sits in the inbound middleware. The backend setup sits in `adapters/outbound/observability/`. Neither touches the domain or application layer.

### Structured logging — standard library `logging` + `ContextVar`

Python's `logging` module, combined with `contextvars`, covers request-scoped structured logging with zero additional dependencies. `ContextVar` is the correct primitive for this — unlike thread-locals, it propagates correctly through `asyncio` tasks, which is exactly the propagation model FastAPI uses.

```python
# adapters/outbound/observability/logging.py
import contextvars
import json
import logging
import os

trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "trace_id": trace_id_var.get(),
        }
        if hasattr(record, "context"):
            payload.update(record.context)
        return json.dumps(payload)

def configure_logging() -> None:
    is_prod = os.environ.get("APP_ENV") == "production"
    handler = logging.StreamHandler()
    handler.setFormatter(
        JSONFormatter() if is_prod
        else logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
```

The trace binding happens once, in middleware:

```python
# adapters/inbound/http/middleware/tracing.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from your_app.adapters.outbound.observability.logging import trace_id_var

class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
        token = trace_id_var.set(trace_id)
        try:
            response = await call_next(request)
            response.headers["x-trace-id"] = trace_id
            return response
        finally:
            trace_id_var.reset(token)
```

Every module then uses the standard pattern — no wrapper class needed:

```python
import logging
log = logging.getLogger(__name__)
log.info("use_case.completed", extra={"context": {"user_id": str(user.id)}})
```

> **Why not `structlog`?** `structlog`'s composable processor pipeline is genuinely cleaner for teams that want small, testable, chainable logging steps, and its `bind()` pattern produces less repetitive call sites than the `extra={"context": {...}}` convention above. The tradeoff is one more dependency and a bridge layer needed so third-party libraries (SQLAlchemy, Alembic, FastAPI) — which all log via the standard `logging` hierarchy — integrate cleanly. For a project prioritising minimal dependencies and standard-library fluency, `logging` + `ContextVar` is the more consistent choice. If the processor-pipeline ergonomics matter more than the dependency count, `structlog` remains a legitimate alternative — swap `adapters/outbound/observability/logging.py` for a `structlog.configure()` call and nothing else in the architecture changes, because the rest of the codebase only ever depends on the *fact* that a logger exists, not on which library provides it.

### What to log at each layer

| Layer | What to log | Level |
|---|---|---|
| HTTP middleware | Request in, response out, latency, status code | INFO |
| Use cases | Started, completed, failed with reason | INFO / ERROR |
| Domain events | Event name, aggregate ID | INFO (audit trail) |
| Outbound adapters | Queries and external calls | DEBUG (never INFO in production) |

Never log: passwords, raw tokens, unmasked PII (email, name, address). The logging adapter's `JSONFormatter` is the right place to mask sensitive context before serialising.

### Metrics and tracing — OpenTelemetry auto-instrumentation

OpenTelemetry auto-instrumentation hooks into FastAPI, SQLAlchemy, and httpx at application startup. This captures request duration, database query time, and outbound HTTP latency without modifying any use case or domain code. Configure it once in `adapters/outbound/observability/tracing.py`. The `trace_id` it generates should be the same one bound to the logging `ContextVar` by `TracingMiddleware`, so every log line and every span share one identifier.

Business metrics — feature adoption, activation events, conversion — are emitted from use cases directly via a lightweight metrics helper injected the same way `UserRepository` is. These are the signals that tell you whether your product is working, not just whether your infrastructure is alive.

### The observability stack — what to add and when

| Stage | What to add | Rationale |
|---|---|---|
| Day one | Sentry free tier | Three lines of code. Groups exceptions, sends alerts on new errors. Covers 80% of operational monitoring needs immediately. |
| First paying user | `logging` JSON output to stdout | Your hosting platform (Fly.io, Railway, Render) aggregates stdout automatically. No additional infrastructure required. |
| Stable recurring revenue | Prometheus + Grafana + Jaeger | The `docker-compose.observability.yml` stack. Worth the investment when infrastructure cost is justified by business need. |

> `docker/docker-compose.observability.yml` contains the full Prometheus + Grafana + Jaeger stack for local use. It is the future state, not the starting point. Run locally with: `make observe`

---

## 7. `container.py` — the composition root

The composition root is the file that makes dependency inversion real rather than theoretical. Without it, the dependency rule is architectural intention with no mechanism behind it. `container.py` is the one place where every port is connected to its concrete adapter — once, at startup, explicitly.

```python
# src/your_app/container.py
from dependency_injector import containers, providers
from your_app.adapters.outbound.persistence.repositories import (
    SqlAlchemyUserRepository,
)
from your_app.adapters.outbound.external.sendgrid import SendGridEmailService
from your_app.application.use_cases.create_user import CreateUserUseCase
from your_app.config import settings

class Container(containers.DeclarativeContainer):

    # Infrastructure resources
    db_session = providers.Resource(create_db_session, url=settings.db_url)

    # Outbound adapters — implement domain ports
    user_repository = providers.Factory(
        SqlAlchemyUserRepository, session=db_session
    )
    email_service = providers.Singleton(
        SendGridEmailService, api_key=settings.sendgrid_key
    )

    # Use cases — receive port ABCs, never concrete adapter classes
    create_user = providers.Factory(
        CreateUserUseCase,
        repo=user_repository,
        email_svc=email_service,
    )
```

> `container.py` is the only file in the codebase where concrete adapter class names appear alongside use case class names. Every other file imports only ABCs (ports) or receives dependencies via FastAPI's `Depends()` mechanism.
>
> If you prefer not to use the `dependency_injector` library, a manual factory function that builds the full dependency graph at startup achieves the same result. The requirement is that wiring is explicit, centralised, and not scattered across modules.

---

## 8. `AGENTS.md` — project brain for AI coding agents

`AGENTS.md` is structured context that any AI coding agent reads before writing, modifying, or suggesting code. It is not documentation for humans — it is a decision guide for automated tools that need to know where code belongs, what is forbidden, and how the architecture is enforced.

### Required sections

| Section | What it contains |
|---|---|
| Architecture overview | One paragraph on ports and adapters, the dependency rule, and the reference to Herberto Graca's Explicit Architecture article |
| The three zones | `domain/`, `application/`, `adapters/` — what each may import, what it contains, what is forbidden |
| SOLID rules as patterns | S: one use case per action. O: new providers = new adapters, not modified ports. L: all adapters implementing a port must be interchangeable. I: small focused port interfaces. D: domain depends on ABCs only, never concrete classes |
| Decision tree | Where to put new code: new business rule, new HTTP endpoint, new database table, new third-party integration |
| Naming conventions | Table: layer, pattern, example. `UserRepository` (ABC), `SqlAlchemyUserRepository` (concrete), `CreateUserUseCase` (use case), `UserCreated` (domain event) |
| Anti-patterns | Business logic in HTTP routers. SQLAlchemy imports in `domain/`. Concrete adapter imports in use cases. Use cases with more than one public method. |
| Testing rules | `unit/`: no I/O, mock all ports by injecting test doubles. `integration/`: real DB against a real adapter. |
| Observability rules | What to log at each layer, what to measure, trace context binding via `ContextVar`, health endpoint contracts, what not to log |

> **AGENTS.md describes the architecture. `import-linter` enforces it.** A document that describes the codebase will eventually describe code that no longer exists. After several months of real development, `AGENTS.md` may say ports live in `domain/ports/` while a refactor moved them elsewhere. An agent reads the stale document and generates code in the wrong place, confidently. The solution is CI enforcement — both are required.

---

## 9. Architecture enforcement with `import-linter`

`import-linter` runs as a required CI step and makes dependency rule violations a broken build. It is the mechanism that keeps `AGENTS.md` honest and the architecture real.

```toml
# pyproject.toml
[tool.importlinter]
root_packages = ["your_app"]

[[tool.importlinter.contracts]]
name = "Domain must not import adapters or external libraries"
type = "forbidden"
source_modules = ["your_app.domain"]
forbidden_modules = ["your_app.adapters", "fastapi", "sqlalchemy", "httpx"]

[[tool.importlinter.contracts]]
name = "Application must not import adapters"
type = "forbidden"
source_modules = ["your_app.application"]
forbidden_modules = ["your_app.adapters"]

[[tool.importlinter.contracts]]
name = "Inbound adapters must not import outbound adapters"
type = "forbidden"
source_modules = ["your_app.adapters.inbound"]
forbidden_modules = ["your_app.adapters.outbound"]
```

Add to `ci.yml` alongside lint and typecheck:

```yaml
- name: Check architecture
  run: uv run lint-imports
```

Add `import-linter` to the dev dependency group in `pyproject.toml`. Add it to `.pre-commit-config.yaml` as well so violations are caught at commit time, before they reach CI.

---

## 10. Root files

### `pyproject.toml` — single source of truth with uv

`uv` reads `pyproject.toml` and writes `uv.lock`. The lockfile is committed. Every developer, every CI run, and every Docker build installs the exact same dependency graph. No `requirements.txt`. No `setup.py`.

```toml
[project]
name = "your-app"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "sentry-sdk>=2.0",
    "opentelemetry-sdk>=1.24",
    "opentelemetry-instrumentation-fastapi>=0.45b0",
    "dependency-injector>=4.41",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.5",
    "mypy>=1.10",
    "pre-commit>=3.7",
    "pip-audit>=2.7",
    "import-linter>=2.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
package = true

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "UP"]

[tool.mypy]
strict = true
```

### `Makefile` — the unified command surface

CI calls the same Makefile targets developers run locally. There is no divergence between what the pipeline does and what a developer does. The architecture check is a first-class target, not an afterthought.

```makefile
.PHONY: install lint typecheck architecture test test-integration \
        check-migrations deploy-staging deploy-prod rollback seed reset-local observe

install:
	uv sync

lint:
	uv run ruff check . && uv run ruff format --check .

typecheck:
	uv run mypy src/

architecture:
	uv run lint-imports

test:
	uv run pytest tests/unit --tb=short

test-integration:
	uv run pytest tests/integration --tb=short

check-migrations:
	uv run python scripts/migrate.py --check

deploy-staging:
	fly deploy --config fly.staging.toml

deploy-prod:
	make check-migrations
	fly deploy --config fly.toml

rollback:
	@fly releases list --config fly.toml
	@read -p "Version: " v; fly deploy --image registry.fly.io/your-app:$$v

seed:
	uv run python scripts/seed.py

reset-local:
	uv run python scripts/reset_db.py

observe:
	docker compose -f docker/docker-compose.yml \
	  -f docker/docker-compose.observability.yml up
```

### `.pre-commit-config.yaml`

Pre-commit runs on `git commit` — the first gate, before code leaves the machine. The `no-commit-to-branch` hook enforces branch discipline structurally: you cannot push directly to main. Gitleaks scans for secrets before they touch the repository at all. Both CI and pre-commit run the same checks — pre-commit gives fast local feedback, CI gives authoritative enforcement nobody can bypass.

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-merge-conflict
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: no-commit-to-branch
        args: [--branch, main]
```

### `.env.example`

Every environment variable the application needs is documented here with placeholder values. This file is committed. The real `.env` is in `.gitignore`. When a new variable is added to `config.py`, `.env.example` is updated in the same pull request — the two are kept in sync by convention and reviewed together.

```bash
# Application
APP_ENV=development            # development | staging | production
SECRET_KEY=change-me

# Database
DATABASE_URL=postgresql://localhost:5432/your_app_dev

# External services
SENTRY_DSN=                    # leave blank to disable locally
SENDGRID_API_KEY=
STRIPE_SECRET_KEY=

# Observability (optional locally)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

---

## 11. How structure connects to the pipeline

| Folder / file | Pipeline layer | How they connect |
|---|---|---|
| `.github/workflows/` | Layer 1, 2, 4 | `ci.yml` runs `make lint`, `make typecheck`, `make architecture`, `make test` on every push. `release.yml` fires on version tag. |
| `domain/` | Layer 1 — Test | Unit tests import only from `domain/` and `application/`. No I/O, no mocks of external systems. The fastest and most valuable tests. |
| `application/use_cases/` | Layer 1 — Test | Unit-tested by injecting mock ABCs. Tests run without a database in under 30 seconds. |
| `adapters/outbound/` | Layer 2 — Deploy | Integration-tested against a real database in staging. Verifies concrete adapters implement their ports correctly. |
| `adapters/inbound/http/middleware/` | Layer 3 — Safety | Trace context binds to every log via `ContextVar`. `/health` and `/ready` endpoints monitored from the first deploy. |
| `container.py` | All layers | Wires the full dependency graph at startup. Implicitly tested by integration tests that exercise the full stack. |
| `AGENTS.md` + `import-linter` | Layer 1 — Foundation | `import-linter` runs in CI on every push. Architecture violations fail the build before any human reviews the code. |
| `Makefile` | All layers | CI calls `make lint`, `make architecture`, `make test`. Staging calls `make deploy-staging`. Production calls `make deploy-prod`. |

---

## 12. Key takeaways

> *"A structure without enforcement is aspiration. The dependency rule is real only when `import-linter` fails the build on the first violation."*

- Ports (abstract base classes) belong in `domain/ports/` — owned by the core, shaped by core needs, never by infrastructure convenience
- Python port interfaces follow the ABC naming convention — `UserRepository`, not `IUserRepository` — consistent with Python's own standard library
- The composition root (`container.py`) is the only file where concrete adapter names and use case names appear together — everything else sees ABCs
- `import-linter` enforces the dependency rule in CI — `AGENTS.md` describes the intention, the build enforces the reality
- CQRS is excluded until you feel the pain — plain use case classes with one `execute()` method are sufficient for any product being built to sell
- An agent orchestration layer was considered and removed — it deserves its own dedicated planning pass, not a bolt-on to the web application structure
- Structured logging uses the standard library `logging` module plus `contextvars` — zero additional dependencies, native integration with every third-party library's own logging
- `structlog` remains a legitimate alternative if its processor-pipeline ergonomics are valued over the dependency saving — the swap is isolated to one file
- The observability stack grows in three stages: Sentry on day one, JSON logs to stdout at first paying user, Prometheus and Grafana at stable revenue
- `uv` replaces pip entirely — `uv.lock` is committed, every developer and CI run installs the exact same dependency graph
- Pre-commit and CI both run the same checks — pre-commit gives fast local feedback, CI gives authoritative enforcement that no one can bypass

*Next: Topic 5 — Secrets and environment management*

---
*Fast Software Delivery — Repo Structure: Python Web Application (Hexagonal)*
