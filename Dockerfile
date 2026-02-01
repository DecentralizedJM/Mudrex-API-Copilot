# Dockerfile for Mudrex API Bot
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data/chroma

# Make startup script executable
RUN chmod +x /app/start.sh

# Environment
ENV PYTHONUNBUFFERED=1

# NO HEALTHCHECK - disable Railway health check in UI instead
CMD ["/app/start.sh"]
