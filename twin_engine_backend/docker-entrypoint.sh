#!/usr/bin/env bash
# ==============================================================
# TwinEngine Backend — Docker Entrypoint
# Handles migrations, static files, and process startup
# ==============================================================
set -euo pipefail

echo "══════════════════════════════════════════════════"
echo " TwinEngine Backend — Starting up"
echo "══════════════════════════════════════════════════"

# ── Run migrations ────────────────────────────────────────────
echo "→ Running database migrations..."
python manage.py migrate --no-input

# ── Collect static files ─────────────────────────────────────
echo "→ Collecting static files..."
python manage.py collectstatic --no-input 2>/dev/null || true

# ── Determine startup mode ───────────────────────────────────
case "${1:-server}" in
    server)
        echo "→ Starting Daphne ASGI server on port ${PORT:-8000}..."
        exec daphne \
            -b 0.0.0.0 \
            -p "${PORT:-8000}" \
            --proxy-headers \
            --access-log - \
            twinengine_core.asgi:application
        ;;
    gunicorn)
        echo "→ Starting Gunicorn WSGI server on port ${PORT:-8000}..."
        exec gunicorn twinengine_core.wsgi:application \
            --bind "0.0.0.0:${PORT:-8000}" \
            --workers "${GUNICORN_WORKERS:-3}" \
            --threads "${GUNICORN_THREADS:-2}" \
            --worker-class gthread \
            --timeout "${GUNICORN_TIMEOUT:-120}" \
            --graceful-timeout 30 \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --access-logfile - \
            --error-logfile - \
            --log-level info
        ;;
    worker)
        echo "→ Starting Celery worker..."
        exec celery -A twinengine_core worker \
            --loglevel="${LOG_LEVEL:-info}" \
            --concurrency="${CELERY_CONCURRENCY:-2}" \
            --max-tasks-per-child=100
        ;;
    beat)
        echo "→ Starting Celery beat scheduler..."
        exec celery -A twinengine_core beat \
            --loglevel="${LOG_LEVEL:-info}" \
            --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;
    *)
        echo "→ Running custom command: $@"
        exec "$@"
        ;;
esac
