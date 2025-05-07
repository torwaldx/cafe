FROM python:3.13.3-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

WORKDIR /app
COPY uv.lock .
COPY pyproject.toml . 

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

ADD ./tg_bot /app/tg_bot

CMD ["uv", "run", "-m", "tg_bot.bot"]