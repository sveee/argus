FROM python:3.11-slim

ENV POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    PATH="/opt/poetry/bin:$PATH" \
    POETRY_NO_INTERACTION=1

RUN apt-get update && \
    apt-get install -y curl build-essential && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Use a clean internal work directory
WORKDIR /app

# Copy only pyproject.toml for installation
COPY . .

RUN poetry install
