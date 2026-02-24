# --- Build Stage ---
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1
# Use copy link mode for optimal layer caching
ENV UV_LINK_MODE=copy

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application
COPY . .
RUN uv sync --frozen --no-dev

# --- Runtime Stage ---
FROM python:3.13-slim

WORKDIR /app

# Copy the virtual environment and app from builder
COPY --from=builder /app /app

# Place the venv's bin directory at the front of PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000

ENV FLASK_APP=main.py

CMD ["uv", "run", "main.py"]