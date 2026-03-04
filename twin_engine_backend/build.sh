#!/usr/bin/env bash
# build.sh — Render / generic PaaS build script
# Set this as your Build Command in Render dashboard

set -o errexit

echo "→ Installing Python dependencies..."
pip install -r requirements.txt

echo "→ Collecting static files..."
python manage.py collectstatic --no-input

echo "→ Running database migrations..."
python manage.py migrate --no-input

echo "✅ Build complete"
