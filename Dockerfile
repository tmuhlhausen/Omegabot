FROM python:3.11-slim

# Security: non-root user
RUN useradd --create-home appuser

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libssl-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy source
COPY src/ src/
COPY backend/ backend/
COPY strategies/ strategies/

# Non-root
USER appuser

# Health endpoint + bot
ENV PORT=8080
CMD exec python -m src.core.engine
