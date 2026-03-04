"""
Celery tasks for the predictive_core app.

- train_models_for_outlet  — retrain all 6 ML models for one outlet
- train_all_outlets         — nightly cron: iterate every active outlet
- send_inventory_alerts     — email low-stock items for one outlet
- send_inventory_alerts_all — morning cron: iterate every active outlet
"""
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────
#  Model Training Tasks
# ──────────────────────────────────────────────────────────

@shared_task(bind=True, name='apps.predictive_core.tasks.train_models_for_outlet',
             max_retries=2, default_retry_delay=60)
def train_models_for_outlet(self, outlet_id: int) -> dict:
    """
    Retrain all ML models for a single outlet.
    Called directly from the TrainModelsView (async) or by the nightly sweep.
    """
    from .ml.prediction_service import PredictionService

    logger.info("Task started: training models for outlet %s", outlet_id)
    try:
        service = PredictionService()
        results = service.train_all(outlet_id)
        logger.info("Training complete for outlet %s: %s", outlet_id, results)
        return {"outlet_id": outlet_id, "status": "complete", "results": results}
    except Exception as exc:
        logger.error("Training failed for outlet %s: %s", outlet_id, exc, exc_info=True)
        raise self.retry(exc=exc)


@shared_task(name='apps.predictive_core.tasks.train_all_outlets')
def train_all_outlets() -> dict:
    """
    Nightly cron job: submit a training task for every active outlet.
    """
    from apps.hospitality_group.models import Outlet

    outlets = Outlet.objects.filter(is_active=True).values_list('id', flat=True)
    submitted = []
    for oid in outlets:
        train_models_for_outlet.delay(oid)
        submitted.append(oid)

    logger.info("Nightly training dispatched for %d outlets: %s", len(submitted), submitted)
    return {"dispatched": len(submitted), "outlet_ids": submitted}


# ──────────────────────────────────────────────────────────
#  Inventory Alert Tasks
# ──────────────────────────────────────────────────────────

@shared_task(bind=True, name='apps.predictive_core.tasks.send_inventory_alerts',
             max_retries=3, default_retry_delay=30)
def send_inventory_alerts(self, outlet_id: int) -> dict:
    """
    Run the inventory predictor for one outlet and email a low-stock
    alert to the brand's contact email if any items are flagged.
    """
    from .ml.prediction_service import PredictionService
    from apps.hospitality_group.models import Outlet

    try:
        outlet = Outlet.objects.select_related('brand').get(id=outlet_id)
    except Outlet.DoesNotExist:
        logger.warning("Outlet %s not found — skipping inventory alert.", outlet_id)
        return {"outlet_id": outlet_id, "status": "skipped", "reason": "not found"}

    service = PredictionService()
    result = service.get_inventory_alerts(outlet_id)

    low_items = result.get('low_stock_items', [])
    if not low_items:
        logger.info("Outlet %s (%s): no low-stock items.", outlet_id, outlet.name)
        return {"outlet_id": outlet_id, "status": "ok", "low_stock_count": 0}

    # Build email
    recipient = outlet.brand.contact_email
    subject = f"[TwinEngine] Low Stock Alert — {outlet.name}"

    html_body = render_to_string('emails/inventory_alert.html', {
        'outlet': outlet,
        'low_items': low_items,
        'total_count': len(low_items),
    })
    plain_body = strip_tags(html_body)

    try:
        send_mail(
            subject=subject,
            message=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_body,
            fail_silently=False,
        )
        logger.info("Inventory alert sent to %s for outlet %s (%d items).",
                     recipient, outlet.name, len(low_items))
    except Exception as exc:
        logger.error("Failed to send inventory alert: %s", exc, exc_info=True)
        raise self.retry(exc=exc)

    return {
        "outlet_id": outlet_id,
        "status": "sent",
        "low_stock_count": len(low_items),
        "recipient": recipient,
    }


@shared_task(name='apps.predictive_core.tasks.send_inventory_alerts_all')
def send_inventory_alerts_all() -> dict:
    """
    Morning cron job: dispatch inventory alert checks for every active outlet.
    """
    from apps.hospitality_group.models import Outlet

    outlets = Outlet.objects.filter(is_active=True).values_list('id', flat=True)
    submitted = []
    for oid in outlets:
        send_inventory_alerts.delay(oid)
        submitted.append(oid)

    logger.info("Inventory alert sweep dispatched for %d outlets.", len(submitted))
    return {"dispatched": len(submitted), "outlet_ids": submitted}
