FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev \
        fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY shared/ /app/shared/
COPY backend/pyproject.toml backend/uv.lock /app/backend/
WORKDIR /app/backend
RUN uv sync --frozen --no-dev

COPY backend/ /app/backend/

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
