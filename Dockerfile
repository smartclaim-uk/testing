# Use Python 3.13 slim image
FROM python:3.13-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY . .

# Install dependencies using uv
RUN uv sync

# Install Playwright browsers
RUN uv run playwright install --with-deps

# Set the default command
CMD ["uv", "run", "python", "-m", "pytest"]