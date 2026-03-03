"""
Demo script: Hit all prediction endpoints using Django test client.
No running server needed -- uses the WSGI app directly.

Usage:  python demo_predictions.py
"""
import os, sys, json

# ---- bootstrap Django ----
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "twinengine_core.settings")

import django
django.setup()

# Add 'testserver' to ALLOWED_HOSTS so the test client works
from django.conf import settings
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

print("=" * 60)
print("  TwinEngine ML Predictions  --  Live Demo")
print("=" * 60)

# authenticate with the synthetic manager
user = User.objects.get(username="synth_mgr_1")
client = APIClient()
client.force_authenticate(user=user)
print(f"[AUTH] Authenticated as {user.username}\n")


def call(label, path):
    print("-" * 60)
    print(f"  {label}")
    print(f"  GET {path}")
    print("-" * 60)
    r = client.get(path)
    try:
        data = r.json()
    except Exception:
        data = str(r.content)
    print(json.dumps(data, indent=2, default=str))
    print()
    return data


# 1. Busy Hours
call("1. BUSY HOURS PREDICTION",
     "/api/predictions/busy-hours/?outlet=4&date=2026-03-04")

# 2. Footfall
call("2. FOOTFALL FORECAST",
     "/api/predictions/footfall/?outlet=4&date=2026-03-04")

# 3. Food Demand
call("3. FOOD DEMAND FORECAST",
     "/api/predictions/food-demand/?outlet=4&date=2026-03-04")

# 4. Revenue
call("4. REVENUE FORECAST",
     "/api/predictions/revenue/?outlet=4&date=2026-03-04")

# 5. Inventory Alerts
call("5. INVENTORY ALERTS",
     "/api/predictions/inventory-alerts/?outlet=4")

# 6. Staffing
call("6. STAFFING RECOMMENDATIONS",
     "/api/predictions/staffing/?outlet=4&date=2026-03-04")

# 7. Full Dashboard
call("7. FULL DASHBOARD (all predictions)",
     "/api/predictions/dashboard/?outlet=4&date=2026-03-04")

print("=" * 60)
print("  Demo complete!")
print("=" * 60)
