# AlphaAlgo Trading Bot - Production Docker Container
# Secure, cloud-ready deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY trading_bot/ ./trading_bot/
COPY config/ ./config/
COPY deploy/ ./deploy/
COPY main.py .
COPY run_unified_bot.py .

# Create required directories
RUN mkdir -p logs data state models reports

# Environment variables (set via docker-compose or runtime)
ENV TRADING_BOT_MODE=paper
ENV TRADING_BOT_LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '.'); from trading_bot.infrastructure.health_endpoints import HealthCheckManager; exit(0)"

# Expose ports
EXPOSE 8080 8081

# Default command - run unified system in paper mode
CMD ["python", "run_unified_bot.py", "--mode", "paper"]
