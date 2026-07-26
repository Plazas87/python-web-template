# python-web-template

A [Copier](https://copier.readthedocs.io/) template for FastAPI web applications built on
Ports & Adapters (Hexagonal) architecture. See `topic4c_repo_structure_hexagonal.md` for the
full architectural rationale this template implements.

## Generating a new app

```bash
uvx copier copy gh:acpr87/python-web-template path/to/new-app
```

You'll be prompted for the project name, package name, description, and author details.

## Pulling template improvements into an already-generated app

```bash
cd path/to/new-app
uvx copier update
```

This re-applies template changes on top of the app's current state, similar to a
`git merge` — conflicts (where both the template and the app changed the same lines) are
left as conflict markers to resolve by hand.

## What this template locks in

- **Templating**: Copier (this file's mechanism)
- **Composition root**: a manual factory (`container.py`), not a DI framework
- **Structured logging**: stdlib `logging` + `contextvars` (no `structlog`)
- **Deploy target**: Railway, via the `railway` CLI in a tag-triggered `release.yml`
- **Config**: `pydantic-settings` reading from `.env`
- **Architecture enforcement**: `import-linter` contracts run in CI and pre-commit

## Repo layout

- `copier.yml` — the prompted variables for generating a new app
- `template/` — the actual Jinja-templated application tree copied into every generated app
- `.github/workflows/test-template.yml` — this repo's own CI: generates a sample app from the
  template and runs its lint/typecheck/architecture/test suite, so template changes are
  verified before they reach anyone using it
