"""
Celery tasks for the insights_hub app.

- generate_report_task  — run the full report pipeline (data → GPT → PDF → Cloudinary)
- email_report_task     — email the finished PDF link to the brand contact
"""
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='apps.insights_hub.tasks.generate_report_task',
             max_retries=2, default_retry_delay=120,
             time_limit=20 * 60, soft_time_limit=18 * 60)
def generate_report_task(self, report_id: int) -> dict:
    """
    Async version of the report-generation pipeline.

    Expects a PDFReport record already created with status='GENERATING'.
    Steps: collect data → GPT-4o → build PDF → upload Cloudinary → update DB.
    On success, dispatches an email notification.
    """
    from .models import PDFReport
    from .services.data_collector import collect_raw_data
    from .services.gpt_report import generate_report_with_gpt, generate_report_fallback
    from apps.cloudinary_service.upload import CloudinaryUploadService
    from apps.insights_hub.views import PDFReportViewSet

    try:
        report = PDFReport.objects.select_related('outlet', 'outlet__brand').get(id=report_id)
    except PDFReport.DoesNotExist:
        logger.error("Report %s not found.", report_id)
        return {"report_id": report_id, "status": "error", "reason": "not found"}

    outlet = report.outlet

    try:
        # ── STEP 1: Collect raw data ──
        logger.info("[Report %d] Step 1: Collecting data for %s (%s → %s)",
                     report_id, outlet.name, report.start_date, report.end_date)
        raw_data = collect_raw_data(outlet, report.start_date, report.end_date)

        # ── STEP 2: GPT-4o (or fallback) ──
        logger.info("[Report %d] Step 2: GPT analysis...", report_id)
        gpt_result = None
        if settings.AZURE_OPENAI_KEY and settings.AZURE_OPENAI_ENDPOINT:
            try:
                gpt_result = generate_report_with_gpt(raw_data)
            except Exception as gpt_err:
                logger.warning("[Report %d] GPT-4o failed, using fallback: %s",
                               report_id, gpt_err)

        if gpt_result is None:
            gpt_result = generate_report_fallback(raw_data)

        executive_summary = gpt_result['executive_summary']
        insights = gpt_result['insights']
        recommendations = gpt_result['recommendations']
        model_used = gpt_result['model_used']

        # ── STEP 3: Build PDF ──
        logger.info("[Report %d] Step 3: Building PDF...", report_id)
        # Instantiate the viewset just to reuse its _build_pdf helper
        viewset = PDFReportViewSet()
        pdf_bytes = viewset._build_pdf(
            outlet=outlet,
            report_type=report.report_type,
            start_date=report.start_date,
            end_date=report.end_date,
            executive_summary=executive_summary,
            insights=insights,
            recommendations=recommendations,
            raw_data=raw_data,
        )

        # ── STEP 4: Upload to Cloudinary ──
        logger.info("[Report %d] Step 4: Uploading to Cloudinary...", report_id)
        cloudinary_url = None
        filename = (
            f"{outlet.name.replace(' ', '_')}_{report.report_type}"
            f"_{report.start_date}_{report.end_date}.pdf"
        )
        upload_result = CloudinaryUploadService.upload_bytes(
            data=pdf_bytes,
            filename=filename,
            folder="reports",
        )
        if upload_result["success"]:
            cloudinary_url = upload_result["url"]
        else:
            logger.warning("[Report %d] Cloudinary upload failed: %s",
                           report_id, upload_result["error"])

        # ── STEP 5: Persist results ──
        report.gpt_summary = executive_summary
        report.insights = insights
        report.recommendations = recommendations
        report.cloudinary_url = cloudinary_url
        report.generated_by = model_used
        report.status = 'COMPLETED'
        report.completed_at = timezone.now()
        report.save()

        logger.info("[Report %d] Completed → %s", report_id, cloudinary_url)

        # Dispatch email notification
        email_report_task.delay(report_id)

        return {
            "report_id": report_id,
            "status": "completed",
            "cloudinary_url": cloudinary_url,
        }

    except Exception as exc:
        logger.error("[Report %d] Failed: %s", report_id, exc, exc_info=True)
        report.status = 'FAILED'
        report.error_message = str(exc)
        report.save()
        raise self.retry(exc=exc)


@shared_task(bind=True, name='apps.insights_hub.tasks.email_report_task',
             max_retries=3, default_retry_delay=30)
def email_report_task(self, report_id: int) -> dict:
    """
    Email the completed report link to the brand contact.
    """
    from .models import PDFReport

    try:
        report = PDFReport.objects.select_related('outlet', 'outlet__brand').get(id=report_id)
    except PDFReport.DoesNotExist:
        return {"report_id": report_id, "status": "skipped", "reason": "not found"}

    if report.status != 'COMPLETED':
        return {"report_id": report_id, "status": "skipped", "reason": "not completed"}

    recipient = report.outlet.brand.contact_email
    subject = (
        f"[TwinEngine] {report.report_type} Report Ready — "
        f"{report.outlet.name} ({report.start_date} to {report.end_date})"
    )

    html_body = render_to_string('emails/report_ready.html', {
        'report': report,
        'outlet': report.outlet,
        'brand': report.outlet.brand,
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
        logger.info("Report email sent to %s for report #%d.", recipient, report_id)
    except Exception as exc:
        logger.error("Report email failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)

    return {"report_id": report_id, "status": "email_sent", "recipient": recipient}
