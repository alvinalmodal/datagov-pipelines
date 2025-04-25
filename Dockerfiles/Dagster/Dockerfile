# Use official Python base image
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# System deps
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && apt-get clean

# Create working directory
WORKDIR /app

# Copy pyproject files and workspace.yaml
COPY pyproject.toml ./
COPY workspace.yaml ./

# Copy all source files (adjust if needed)
COPY ./src ./src

# Install dependencies using uv
RUN uv sync

# Expose Dagster webserver port
EXPOSE 3000

# Default to webserver (you can override to daemon)
CMD ["uv", "run", "dagster", "dev", "-h", "0.0.0.0", "-p", "3000"]