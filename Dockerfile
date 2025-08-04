# Use an official base image with Python 3.12.10
FROM python:3.12.10-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Python packaging tool) and add it to PATH
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Create venv and install in editable mode
RUN uv pip install -e . --system

# Default command
CMD ["python"]