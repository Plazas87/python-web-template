FROM python:{{ python_version }}-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev


FROM python:{{ python_version }}-slim AS runtime

WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/src ./src

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "{{ package_name }}.main:app", "--host", "0.0.0.0", "--port", "8000"]
