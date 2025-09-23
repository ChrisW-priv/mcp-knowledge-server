# This Dockerfile will build backend for app assuming the build context is the root of project directory
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:fcb50226f56cc30eb2d9fab234e1d15c2f26103b84b15d6e39ba75ed17c71876 AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_PREFERENCE='only-system'

COPY pyproject.toml .

RUN uv sync --no-dev

FROM python:3.13-slim@sha256:f41a75c9cee9391c09e0139f7b49d4b1fbb119944ec740ecce4040626dc07bed AS default-service-target

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y pandoc

COPY --from=base /app /app

WORKDIR /app/backend

COPY backend/ /app/backend
COPY mcp/ /app/mcp
COPY fastagent.config.yaml /app

COPY backend/backend/deployed_settings/ /app/backend/backend/settings/

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["/app/backend/entrypoint.sh", "run_asgi"]
