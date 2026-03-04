"""
Celery application configuration for TwinEngine.

- Uses Redis as the message broker and result backend.
- Auto-discovers tasks in every installed app.
- Serialises results as JSON for easy inspection.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twinengine_core.settings')

app = Celery('twinengine')

# Pull all CELERY_* settings from Django settings (namespace='CELERY')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in each installed app
app.autodiscover_tasks()

# ── Default periodic tasks (Celery Beat) ──
app.conf.beat_schedule = {
    'nightly-model-retraining': {
        'task': 'apps.predictive_core.tasks.train_all_outlets',
        'schedule': crontab(hour=2, minute=0),       # every day at 02:00
        'options': {'queue': 'ml'},
    },
    'morning-inventory-alerts': {
        'task': 'apps.predictive_core.tasks.send_inventory_alerts_all',
        'schedule': crontab(hour=7, minute=0),        # every day at 07:00
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Sanity-check task — prints its own request info."""
    print(f'Request: {self.request!r}')
