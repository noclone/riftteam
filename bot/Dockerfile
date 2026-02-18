FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY shared/ /app/shared/
COPY bot/pyproject.toml bot/uv.lock /app/bot/
WORKDIR /app/bot
RUN uv sync --frozen --no-dev

COPY bot/ /app/bot/

CMD ["uv", "run", "python", "bot.py"]
