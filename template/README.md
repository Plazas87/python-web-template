# {{ project_name }}

{{ description }}

## Architecture

Ports & Adapters (Hexagonal). Dependencies point inward only: `adapters/` depends on
`domain/` ports and external libraries, `application/` depends on `domain/` only, `domain/`
depends on nothing outside itself. See `AGENTS.md` for the full rules — it's the document
AI coding agents (and humans) should read before adding code.

## What's included

Working vertical slices to copy the pattern from, not an empty skeleton:

- **Auth**: `POST /auth/register`, `POST /auth/login` (JWT), `GET /auth/me`
- **Authorization**: `GET /users` (admin-only), gated by a domain-level `Policy` port —
  see "Authentication vs. authorization" in `AGENTS.md`
- **Pagination**: `GET /users?page=&page_size=` — see `domain/model/pagination.py`
- **File storage**, **background jobs** (in-process scheduler), and **domain events** (with
  a working audit-log consumer) — each documented in its own `AGENTS.md` section

## Getting started

```bash
make install
cp .env.example .env
docker compose -f docker/docker-compose.yml up -d db
make reset-local
uv run uvicorn {{ package_name }}.main:app --reload
```

## Common commands

| Command | What it does |
|---|---|
| `make lint` | Ruff check + format check |
| `make typecheck` | mypy strict |
| `make architecture` | import-linter — fails the build on a dependency-rule violation |
| `make test` | Unit tests (`tests/unit`, no I/O) |
| `make test-integration` | Integration tests against a real DB |
| `make seed` | Insert demo data, incl. a working admin login for local dev |
| `make deploy-staging` / `make deploy-prod` | Deploy to Railway |

## Deployment

Deploys to [Railway](https://railway.app) via the `railway` CLI, triggered from
`.github/workflows/release.yml` on a `v*` tag push. Requires a `RAILWAY_TOKEN` secret set
in this repo's GitHub Actions settings. Staging and production are separate Railway
environments within the same project.
