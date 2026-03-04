# ==============================================================
# TwinEngine Backend — Multi-stage Production Dockerfile
# Compatible with: Azure App Service, Azure Container Apps, Render
# ==============================================================

# ── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install system dependencies for Python packages (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libjpeg62-turbo-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="TwinEngine <contact@twinengine.io>"
LABEL description="TwinEngine Hospitality Backend — AI-powered digital twin"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=twinengine_core.settings \
    CONTAINER=true \
    PORT=8000

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system app \
    && adduser --system --ingroup app app

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p logs media staticfiles \
    && python manage.py collectstatic --no-input 2>/dev/null || true \
    && chown -R app:app /app

# Entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER app

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["server"]
