# Multi-stage Docker build for stock market data pipeline
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Development stage
FROM base as development

# Install development dependencies
RUN uv sync --frozen --extra dev

# Copy source code
COPY . .

# Set Python path
ENV PYTHONPATH=/app/src

# Default command for development
CMD ["bash"]

# Production stage
FROM base as production

# Copy only production dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/
COPY dags/ ./dags/
COPY dataproc_jobs/ ./dataproc_jobs/
COPY data/ ./data/

# Set Python path
ENV PYTHONPATH=/app/src

# Create non-root user
RUN groupadd -r pipeline && useradd -r -g pipeline pipeline
RUN chown -R pipeline:pipeline /app
USER pipeline

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command for development/testing
CMD ["bash"]
