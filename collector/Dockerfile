FROM selenium/standalone-chrome:135.0.7049.84-chromedriver-135.0.7049.84-20250414

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Enable bytecode compilation
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app
COPY uv.lock .
COPY pyproject.toml . 

RUN --mount=type=cache,target=/root/.cache/uv \
    sudo uv sync --no-install-project --no-dev

COPY collector collector

CMD ["uv", "run", "-m", "collector.scheduler"]
