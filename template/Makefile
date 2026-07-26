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
	railway up --service {{ project_slug }} --environment staging

deploy-prod:
	make check-migrations
	railway up --service {{ project_slug }} --environment production

rollback:
	@echo "Railway CLI has no scriptable rollback — redeploy a previous build from the Railway dashboard."

seed:
	uv run python scripts/seed.py

reset-local:
	uv run python scripts/reset_db.py

observe:
	docker compose -f docker/docker-compose.yml \
	  -f docker/docker-compose.observability.yml up
