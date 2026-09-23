# python-web-template

A [Copier](https://copier.readthedocs.io/) template for spinning up new FastAPI web
services fast, without re-deciding your architecture every time. Generate a project,
answer a few prompts, and you get a working app with:

- **Ports & Adapters (Hexagonal) architecture** — business logic that doesn't know
  FastAPI or SQLAlchemy exist, so you can test it in milliseconds and swap infrastructure
  without rewriting it
- Working vertical slices wired end to end, so you copy a working pattern instead of
  starting from an empty folder: registration + JWT login (`POST /auth/register`,
  `POST /auth/login`, `GET /auth/me`), a role-based authorization example
  (`GET /users`, admin-only), and a plain CRUD example (`POST /users`)
- A domain-level `Policy` port for authorization rules that must hold no matter what calls
  the use case — not just an HTTP route guard a background job or script could bypass
- A `Page`/`PageRequest` pagination pattern on the repository port, a `FileStorageService`
  port (local-disk adapter, swappable for S3-compatible storage), an in-process
  scheduled-jobs story (APScheduler by default, documented upgrade path to Celery/RQ), and
  a domain-events dispatcher with a working audit-log consumer
- CI that lints, typechecks, and **enforces the architecture** (a build fails if someone
  imports SQLAlchemy into your domain layer — see [Architecture](#architecture))
- `/health` + `/ready` endpoints, structured JSON logging with request tracing, and
  Prometheus metrics, all wired up before you write your first feature
- Docker, Alembic migrations, and a tag-triggered deploy to [Railway](https://railway.app)

## Quickstart

Generate a new app:

```bash
uvx copier copy gh:Plazas87/python-web-template my-new-app
```

You'll be prompted for:

| Prompt | Example | Used for |
|---|---|---|
| `project_name` | `Acme Billing API` | Display name, `AGENTS.md`, `README.md` |
| `project_slug` | `acme-billing` (auto-derived) | Docker image name, Railway service name, `pyproject.toml` name |
| `package_name` | `acme_billing` (auto-derived) | The importable Python package (`src/acme_billing/...`) |
| `description` | `Billing service for Acme` | One-line description in `pyproject.toml` / `README.md` |
| `author_name`, `author_email` | | `pyproject.toml` metadata |
| `python_version` | `3.12` | Minimum Python version |

Then run it locally:

```bash
cd my-new-app
make install                    # uv sync
cp .env.example .env
docker compose -f docker/docker-compose.yml up -d db
make reset-local                # create tables
uv run uvicorn acme_billing.main:app --reload
```

```bash
curl http://localhost:8000/health
# {"status":"ok"}

curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "jane@example.com", "name": "Jane", "password": "s3cret123"}'
# {"id":"...", "email":"jane@example.com", "name":"Jane", "roles":["user"]}

curl -X POST http://localhost:8000/auth/login \
  -d "username=jane@example.com&password=s3cret123"
# {"access_token":"...", "token_type":"bearer"}
```

## What you get

```text
my-new-app/
├── src/acme_billing/
│   ├── domain/              # entities, value objects, port interfaces (ABCs) — zero external imports
│   ├── application/         # use cases — one class per business action
│   ├── adapters/
│   │   ├── inbound/http/       # FastAPI routes, middleware, request/response schemas
│   │   ├── inbound/scheduler/  # background job functions (in-process APScheduler)
│   │   └── outbound/           # SQLAlchemy repositories, security (hashing/JWT/policy),
│   │                           # events, file storage, external clients, observability
│   ├── container.py         # composition root — wires every port to its adapter, once
│   ├── config.py            # pydantic-settings, reads .env
│   └── main.py               # FastAPI app entrypoint
├── tests/
│   ├── unit/                # domain + application, no I/O, runs in milliseconds
│   └── integration/         # exercises the real FastAPI app
├── docker/                  # Dockerfile, docker-compose (app + Postgres), observability stack
├── .github/workflows/       # ci.yml (lint/typecheck/architecture/test), release.yml (deploy)
├── AGENTS.md                # architecture rules for AI coding agents and humans
└── Makefile                 # the single command surface — CI runs the same targets you do
```

## Architecture

Dependencies point inward, only. `domain/` depends on nothing. `application/` depends on
`domain/` only. `adapters/` depend on `domain/` ports and whatever external library they
wrap.

| Zone | Can import | Holds |
|---|---|---|
| `domain/` | nothing outside itself | entities, value objects, port interfaces (ABCs), domain events |
| `application/` | `domain/` only | use cases — one class per business action, one public method (`execute`) |
| `adapters/` | `domain/` ports + external libs | FastAPI routers, SQLAlchemy repositories, external API clients |

The payoff: swap Postgres for something else, or SendGrid for Postmark, by writing one new
adapter class — nothing in `domain/` or `application/` changes, because they only ever
depend on the abstract port (`UserRepository`, `EmailService`), never the concrete class.

This isn't just a convention — `import-linter` contracts in `pyproject.toml` run in CI and
pre-commit and **fail the build** if `domain/` imports `fastapi`, or `application/` imports
an adapter, or an inbound adapter reaches into an outbound one. See `AGENTS.md` in a
generated app for the full rule set, naming conventions, and where to put new code.

## Example: adding a feature

Say you want `DELETE /users/{id}`. The pattern to follow, in order:

1. **Use case** — `application/use_cases/delete_user.py`, one class, one `execute` method,
   taking the same `UserRepository` port the existing `CreateUserUseCase` takes.
2. **Route** — add a handler to `adapters/inbound/http/router.py` that validates the path
   parameter, calls the use case via the same `Depends()` pattern already used for
   `create_user`, and returns a response. No business logic in the route itself.
3. **Wiring** — nothing to do; `container.py` already builds a `UserRepository` per
   request, so the new use case gets it the same way `CreateUserUseCase` does.
4. **Tests** — a unit test in `tests/unit/application/` injecting a fake `UserRepository`
   (copy the pattern in `test_create_user.py`), no database needed.

If instead you needed a new *integration* (say, charging a card), the port goes in
`domain/ports/services.py`, the concrete adapter goes in `adapters/outbound/external/`, and
it's wired in `container.py`. `AGENTS.md`'s decision tree covers this in more detail, along
with the same one-new-file shape for: an authorization rule (the `Policy` port), something
that should run on a schedule (`adapters/inbound/scheduler/jobs.py`), reacting to a domain
event (`EventDispatcher`), and a new paginated list endpoint (`Page`/`PageRequest`).

## Testing

```bash
make test              # unit tests — domain + application, no I/O
make test-integration   # integration tests — real FastAPI app via TestClient
```

Unit tests inject fake port implementations (see `tests/unit/application/test_create_user.py`)
instead of mocking — a fake is a few lines of plain Python implementing the same ABC the
real adapter implements, and it can't silently drift from the real interface the way a mock
can.

## Deployment

Deploys to [Railway](https://railway.app) via the `railway` CLI, triggered by
`.github/workflows/release.yml` on a `v*` tag push:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Requires a `RAILWAY_TOKEN` secret set on the generated repo (Settings → Secrets → Actions).
Staging and production map to separate Railway environments within the same project —
`make deploy-staging` / `make deploy-prod` run the same `railway up` command a developer
would run locally, just with a different `--environment` flag.

## Updating a generated app when the template improves

```bash
cd my-new-app
uvx copier update
```

This replays the template's changes on top of the app's current state, similar to a
`git merge` — where both the template and the app changed the same lines, you get conflict
markers to resolve by hand, same as any merge.

## Key decisions this template makes for you

| Decision | Choice | Why |
|---|---|---|
| Composition root | A plain `Container` dataclass with a `build()` factory method — no DI framework | One file, ordinary Python, nothing new to learn to read the whole dependency graph |
| Structured logging | Standard library `logging` + `contextvars` | Zero extra dependencies; integrates natively with FastAPI/SQLAlchemy/Alembic's own logging, which already goes through `logging` |
| Config | `pydantic-settings` reading `.env` | Typed, validated settings instead of raw `os.environ` calls |
| Password hashing | `argon2-cffi`, used directly | `passlib` (the more commonly reached-for choice) is unmaintained — no release since 2020, already breaking under current `bcrypt`/Python |
| Access tokens | `PyJWT` | FastAPI's own docs moved their tutorial to PyJWT in Aug 2026; the alternative, `python-jose`, carries an unpatched vulnerability in its `ecdsa` dependency |
| Authorization | A domain-level `Policy` port, checked *inside* the use case, not only an HTTP dependency | An HTTP-only guard can be bypassed by any non-HTTP caller — a background job, a script, another adapter |
| Background jobs | In-process `AsyncIOScheduler` (APScheduler) by default | Zero extra infrastructure; graduate to Celery/RQ + Redis only once there's real queueing/retry/distributed-worker need |
| Deploy target | Railway, CLI-driven, tag-triggered | Keeps the deploy trigger as auditable code in `release.yml` rather than hidden dashboard config |
| CQRS, event sourcing, a shared kernel | Not included (a simple in-process domain-event dispatcher is — see `domain/events.py`) | Full CQRS/event sourcing solve problems at a scale most new services haven't hit yet — add them when the pain shows up, not before |

If a choice above doesn't fit your project, it's meant to be changed — swap the logging
module, drop in a different deploy target, add CQRS later. Nothing in `domain/` or
`application/` depends on any of these choices, by construction.
