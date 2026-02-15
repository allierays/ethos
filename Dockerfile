# Stage 1: Build dependencies
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock LICENSE README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY ethos/ ethos/
COPY api/ api/
COPY scripts/ scripts/
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN useradd --system --no-create-home app

COPY --from=builder /app/.venv /app/.venv
COPY ethos/ ethos/
COPY api/ api/
COPY scripts/ scripts/

USER app

EXPOSE 8000

CMD ["/app/.venv/bin/python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
