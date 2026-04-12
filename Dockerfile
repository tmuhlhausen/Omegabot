FROM python:3.11-slim

# Security: non-root user
RUN useradd --create-home appuser

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libssl-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (constraints kept alongside requirements for repeatability)
COPY requirements.txt constraints-shared.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy source + database migrations + alembic config
COPY src/ src/
COPY backend/ backend/
COPY strategies/ strategies/
COPY migrations/ migrations/
COPY alembic.ini ./
COPY VERSION ./

# Non-root
USER appuser

# Health endpoint + bot
ENV PORT=8080
CMD exec python -m src.core.engine
