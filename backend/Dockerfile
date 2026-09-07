# Backend Dockerfile for Abraxas Routing Platform
FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies for C extensions (igraph, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml .

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source code and scripts
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV MONGO_URI=mongodb://mongodb:27017/logistics_db

EXPOSE 8000

# Run pre-flight healthcheck and start uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
