import logging
from io import BytesIO

from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, ListFlowable, ListItem,
)

from apps.cloudinary_service.upload import CloudinaryUploadService
from .models import DailySummary, PDFReport
from .serializers import (
    DailySummarySerializer, DailySummaryListSerializer, DailySummaryCreateSerializer,
    PDFReportSerializer, PDFReportListSerializer,
    ReportGenerateSerializer, DailyReportResponseSerializer
)
from .services.data_collector import collect_raw_data
from .services.gpt_report import generate_report_with_gpt, generate_report_fallback
from twinengine_core.throttles import ReportRateThrottle

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Reports'], summary='List all daily summaries'),
    create=extend_schema(tags=['Reports'], summary='Create a daily summary'),
    retrieve=extend_schema(tags=['Reports'], summary='Retrieve a daily summary'),
    update=extend_schema(tags=['Reports'], summary='Update a daily summary'),
    partial_update=extend_schema(tags=['Reports'], summary='Partial update a daily summary'),
    destroy=extend_schema(tags=['Reports'], summary='Delete a daily summary'),
)
class DailySummaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Daily Summaries.
    
    Endpoints:
    - GET /api/summaries/ - List all daily summaries
    - POST /api/summaries/ - Create a new summary
    - GET /api/summaries/{id}/ - Retrieve summary
    - GET /api/summaries/trends/ - Get trends over time
    - GET /api/summaries/compare/ - Compare outlets
    """
    queryset = DailySummary.objects.select_related('outlet').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['outlet', 'date', 'outlet__brand']
    ordering_fields = ['date', 'total_revenue', 'total_orders']
    ordering = ['-date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DailySummaryCreateSerializer
        if self.action == 'list':
            return DailySummaryListSerializer
        return DailySummarySerializer
    
    @extend_schema(tags=['Reports'], summary='Get performance trends over time', parameters=[
        OpenApiParameter('outlet', OpenApiTypes.INT, description='Filter by outlet ID'),
        OpenApiParameter('days', OpenApiTypes.INT, description='Number of days to look back (default 30)'),
    ])
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get performance trends over time."""
        outlet_id = request.query_params.get('outlet')
        try:
            days = int(request.query_params.get('days', 30))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid "days" parameter. Must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        qs = self.queryset.filter(date__gte=start_date)
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        # Daily aggregates
        daily = qs.values('date').annotate(
            revenue=Sum('total_revenue'),
            orders=Sum('total_orders'),
            guests=Sum('total_guests'),
            avg_wait=Avg('avg_wait_time')
        ).order_by('date')
        
        return Response(list(daily))
    
    @extend_schema(tags=['Reports'], summary='Compare performance across outlets', parameters=[
        OpenApiParameter('brand', OpenApiTypes.INT, description='Filter by brand ID'),
        OpenApiParameter('days', OpenApiTypes.INT, description='Number of days to compare (default 7)'),
    ])
    @action(detail=False, methods=['get'])
    def compare(self, request):
        """Compare performance across outlets."""
        brand_id = request.query_params.get('brand')
        try:
            days = int(request.query_params.get('days', 7))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid "days" parameter. Must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        qs = self.queryset.filter(date__gte=start_date)
        if brand_id:
            qs = qs.filter(outlet__brand_id=brand_id)
        
        # Aggregate by outlet
        by_outlet = qs.values('outlet', 'outlet__name').annotate(
            total_revenue=Sum('total_revenue'),
            total_orders=Sum('total_orders'),
            avg_ticket=Avg('avg_ticket_size'),
            avg_wait=Avg('avg_wait_time')
        ).order_by('-total_revenue')
        
        return Response(list(by_outlet))
    
    @extend_schema(tags=['Reports'], summary="Get today's summaries", parameters=[
        OpenApiParameter('outlet', OpenApiTypes.INT, description='Filter by outlet ID'),
    ], responses={200: DailySummarySerializer(many=True)})
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's summary (or generate one)."""
        outlet_id = request.query_params.get('outlet')
        today = timezone.now().date()
        
        qs = self.queryset.filter(date=today)
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        summaries = DailySummarySerializer(qs, many=True).data
        return Response(summaries)


@extend_schema_view(
    list=extend_schema(tags=['Reports'], summary='List all PDF reports'),
    create=extend_schema(tags=['Reports'], summary='Create a PDF report record'),
    retrieve=extend_schema(tags=['Reports'], summary='Retrieve a PDF report'),
    update=extend_schema(tags=['Reports'], summary='Update a PDF report'),
    partial_update=extend_schema(tags=['Reports'], summary='Partial update a PDF report'),
    destroy=extend_schema(tags=['Reports'], summary='Delete a PDF report'),
)
class PDFReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing PDF Reports.
    
    Endpoints:
    - GET /api/reports/ - List all reports
    - POST /api/reports/ - Create a new report
    - GET /api/reports/{id}/ - Retrieve report details
    - POST /api/reports/generate/ - Generate a new report using GPT-4
    """
    queryset = PDFReport.objects.select_related('outlet').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['outlet', 'report_type', 'status', 'outlet__brand']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-created_at']
    throttle_classes = [ReportRateThrottle]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PDFReportListSerializer
        return PDFReportSerializer
    
    @extend_schema(
        tags=['Reports'],
        summary='Generate AI report (async via Celery or sync)',
        request=ReportGenerateSerializer,
        responses={202: PDFReportSerializer, 201: PDFReportSerializer, 400: None, 500: None},
    )
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate Report — Full Pipeline (defaults to ASYNC via Celery):
          1. Create a GENERATING report record
          2. Dispatch Celery task (data → GPT → PDF → Cloudinary → email)
          3. Return 202 with task_id for polling

        Pass ?sync=true to run the entire pipeline in-request (original behaviour).
        """
        serializer = ReportGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from apps.hospitality_group.models import Outlet

        outlet_id = serializer.validated_data['outlet_id']
        report_type = serializer.validated_data['report_type']
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']

        outlet = Outlet.objects.get(id=outlet_id)

        # ── Create a PENDING report record so frontend can show progress ──
        report = PDFReport.objects.create(
            outlet=outlet,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            status='GENERATING',
            generated_by='GPT-4o',
        )

        # ── Check if caller wants synchronous execution ──
        run_sync = request.query_params.get('sync', 'false').lower() == 'true'

        if not run_sync:
            # Dispatch to Celery
            from .tasks import generate_report_task
            task = generate_report_task.delay(report.pk)
            return Response(
                {
                    **PDFReportSerializer(report).data,
                    "task_id": task.id,
                    "poll_url": f"/api/tasks/{task.id}/",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        # ── Synchronous path (backward compat / testing) ──
        try:
            # ── STEP 1: Collect raw data from all models ──
            logger.info("Step 1: Collecting raw data for %s (%s -> %s)", outlet.name, start_date, end_date)
            raw_data = collect_raw_data(outlet, start_date, end_date)

            # ── STEP 2: Send to GPT-4o (or fallback) ──
            logger.info("Step 2: Sending data to GPT-4o...")
            gpt_result = None
            if settings.AZURE_OPENAI_KEY and settings.AZURE_OPENAI_ENDPOINT:
                try:
                    gpt_result = generate_report_with_gpt(raw_data)
                    logger.info("GPT-4o report generated (model: %s)", gpt_result.get('model_used'))
                except Exception as gpt_err:
                    logger.warning("GPT-4o failed, falling back to local generator: %s", gpt_err)

            if gpt_result is None:
                logger.info("Using fallback report generator")
                gpt_result = generate_report_fallback(raw_data)

            executive_summary = gpt_result['executive_summary']
            insights = gpt_result['insights']
            recommendations = gpt_result['recommendations']
            model_used = gpt_result['model_used']

            # ── STEP 3: Build PDF from GPT output ──
            logger.info("Step 3: Building PDF...")
            pdf_bytes = self._build_pdf(
                outlet=outlet,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                executive_summary=executive_summary,
                insights=insights,
                recommendations=recommendations,
                raw_data=raw_data,
            )

            # ── STEP 4: Upload PDF to Cloudinary ──
            logger.info("Step 4: Uploading PDF to Cloudinary...")
            cloudinary_url = None
            filename = (
                f"{outlet.name.replace(' ', '_')}_{report_type}"
                f"_{start_date}_{end_date}.pdf"
            )
            upload_result = CloudinaryUploadService.upload_bytes(
                data=pdf_bytes,
                filename=filename,
                folder="reports",
            )
            if upload_result["success"]:
                cloudinary_url = upload_result["url"]
                logger.info("PDF uploaded -> %s", cloudinary_url)
            else:
                logger.warning("PDF upload failed: %s", upload_result["error"])

            # ── STEP 5: Update report record ──
            report.gpt_summary = executive_summary
            report.insights = insights
            report.recommendations = recommendations
            report.cloudinary_url = cloudinary_url
            report.generated_by = model_used
            report.status = 'COMPLETED'
            report.completed_at = timezone.now()
            report.save()

            logger.info("Report #%d completed -> %s", report.pk, cloudinary_url)

            # Send email notification directly (sync path — no need for Celery)
            try:
                recipient = outlet.brand.contact_email
                subject = (
                    f"[TwinEngine] {report_type} Report Ready — "
                    f"{outlet.name} ({start_date} to {end_date})"
                )
                html_body = render_to_string('emails/report_ready.html', {
                    'report': report,
                    'outlet': outlet,
                    'brand': outlet.brand,
                })
                plain_body = strip_tags(html_body)
                from django.core.mail import send_mail as django_send_mail
                django_send_mail(
                    subject=subject,
                    message=plain_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    html_message=html_body,
                    fail_silently=False,
                )
                logger.info("Report email sent to %s for report #%d.", recipient, report.pk)

                # ── Gmail copy (dual delivery) ──
                import smtplib, ssl
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                gmail_email = getattr(settings, 'GMAIL_EMAIL', '')
                gmail_password = getattr(settings, 'GMAIL_APP_PASSWORD', '')
                if gmail_email and gmail_password:
                    try:
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From'] = gmail_email
                        msg['To'] = gmail_email
                        msg.attach(MIMEText(plain_body, 'plain'))
                        msg.attach(MIMEText(html_body, 'html'))
                        ctx = ssl.create_default_context()
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ctx) as srv:
                            srv.login(gmail_email, gmail_password)
                            srv.sendmail(gmail_email, gmail_email, msg.as_string())
                        logger.info("Gmail copy sent for report #%d.", report.pk)
                    except Exception as gmail_err:
                        logger.warning("Gmail copy failed (report still saved): %s", gmail_err)

            except Exception as mail_err:
                logger.warning("Email sending failed (report still saved): %s", mail_err)

            return Response(
                PDFReportSerializer(report).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            logger.error("Report generation failed: %s", exc, exc_info=True)
            report.status = 'FAILED'
            report.error_message = str(exc)
            report.save()
            return Response(
                {"error": f"Report generation failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ──────────────────────────────────────────────────────────
    #  PDF Builder — turns GPT output into a beautiful PDF
    # ──────────────────────────────────────────────────────────

    def _build_pdf(self, outlet, report_type, start_date, end_date,
                   executive_summary, insights, recommendations, raw_data):
        """
        Build a professional multi-section PDF and return raw bytes.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=20 * mm, rightMargin=20 * mm,
            topMargin=25 * mm, bottomMargin=20 * mm,
        )
        styles = getSampleStyleSheet()

        # ── Custom styles ──
        BRAND_BLUE = HexColor('#2980b9')
        DARK = HexColor('#2c3e50')
        LIGHT_BG = HexColor('#ecf0f1')
        WHITE = HexColor('#ffffff')
        BORDER_GREY = HexColor('#bdc3c7')
        RED = HexColor('#e74c3c')
        GREEN = HexColor('#27ae60')

        title_style = ParagraphStyle(
            'RTitle', parent=styles['Title'],
            fontSize=24, textColor=DARK, spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            'RSubtitle', parent=styles['Normal'],
            fontSize=11, textColor=HexColor('#7f8c8d'), spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            'RHeading', parent=styles['Heading2'],
            fontSize=15, textColor=BRAND_BLUE, spaceBefore=18, spaceAfter=8,
        )
        body_style = ParagraphStyle(
            'RBody', parent=styles['BodyText'],
            fontSize=10.5, leading=16, spaceAfter=4,
        )
        bullet_style = ParagraphStyle(
            'RBullet', parent=body_style,
            leftIndent=15, bulletIndent=5, spaceAfter=3,
        )
        footer_style = ParagraphStyle(
            'RFooter', parent=styles['Normal'],
            fontSize=8, textColor=HexColor('#95a5a6'), alignment=1,
        )

        elements = []

        # ── Header ──
        elements.append(Paragraph("TwinEngine Hospitality", title_style))
        elements.append(Paragraph(
            f"{report_type} Operations Report &nbsp;|&nbsp; "
            f"{outlet.name} ({outlet.brand.name}) &nbsp;|&nbsp; "
            f"{start_date} to {end_date}",
            subtitle_style,
        ))
        elements.append(HRFlowable(
            width="100%", thickness=1.5, color=BRAND_BLUE,
            spaceBefore=2, spaceAfter=12,
        ))

        # ── Key Metrics Table ──
        order_s = raw_data.get('order_summary', {})
        payment_s = raw_data.get('payment_summary', {})
        table_s = raw_data.get('table_overview', {})

        total_rev = order_s.get('total_revenue', 0) or 0
        total_ord = order_s.get('total_orders', 0) or 0
        total_gst = order_s.get('total_guests', 0) or 0
        avg_wait = order_s.get('avg_wait_minutes', 0) or 0
        avg_ticket = order_s.get('avg_ticket', 0) or 0
        total_tips = payment_s.get('total_tips', 0) or 0

        elements.append(Paragraph("Key Performance Metrics", heading_style))
        metrics_data = [
            ['Total Revenue', f'Rs.{total_rev:,.2f}',   'Total Orders', f'{total_ord:,}'],
            ['Total Guests',  f'{total_gst:,}',        'Avg Ticket',   f'Rs.{avg_ticket:,.2f}'],
            ['Avg Wait Time', f'{avg_wait:.1f} min',   'Tips Earned',  f'Rs.{total_tips:,.2f}'],
            ['Tables',        f'{table_s.get("total_tables", "-")}',
             'Capacity',      f'{table_s.get("total_capacity", "-")} seats'],
        ]
        t = Table(metrics_data, colWidths=[110, 110, 110, 110])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_BG),
            ('BACKGROUND', (2, 0), (2, -1), LIGHT_BG),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6 * mm))

        # ── Order Status Breakdown ──
        status_bd = order_s.get('status_breakdown', {})
        if status_bd:
            elements.append(Paragraph("Order Status Breakdown", heading_style))
            status_rows = [['Status', 'Count']]
            status_colors = {
                'COMPLETED': GREEN, 'SERVED': GREEN,
                'CANCELLED': RED,
                'PLACED': HexColor('#f39c12'), 'PREPARING': HexColor('#f39c12'),
            }
            for st, cnt in status_bd.items():
                status_rows.append([st, str(cnt)])
            st_table = Table(status_rows, colWidths=[200, 100])
            st_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(st_table)
            elements.append(Spacer(1, 6 * mm))

        # ── Payment Methods ──
        pay_methods = payment_s.get('methods_breakdown', {})
        if pay_methods:
            elements.append(Paragraph("Payment Methods", heading_style))
            pay_rows = [['Method', 'Transactions']]
            for method, cnt in pay_methods.items():
                pay_rows.append([method, str(cnt)])
            pay_table = Table(pay_rows, colWidths=[200, 100])
            pay_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(pay_table)
            elements.append(Spacer(1, 6 * mm))

        # ── Low Stock Alerts ──
        inv = raw_data.get('inventory_summary', {})
        low_items = inv.get('low_stock_items', [])
        if low_items:
            elements.append(Paragraph("[!] Low Stock Alerts", heading_style))
            inv_rows = [['Item', 'Category', 'Current Qty', 'Reorder At']]
            for item in low_items[:10]:
                inv_rows.append([
                    item['name'], item['category'],
                    f"{item['current_quantity']} {item.get('unit', '')}",
                    f"{item['reorder_threshold']} {item.get('unit', '')}",
                ])
            inv_table = Table(inv_rows, colWidths=[120, 90, 100, 100])
            inv_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), RED),
                ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, HexColor('#fdf2f2')]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(inv_table)
            elements.append(Spacer(1, 6 * mm))

        # ── Executive Summary (from GPT-4o) ──
        elements.append(HRFlowable(
            width="100%", thickness=0.5, color=BORDER_GREY,
            spaceBefore=6, spaceAfter=6,
        ))
        elements.append(Paragraph("Executive Summary", heading_style))
        for para in executive_summary.strip().split('\n\n'):
            clean = para.strip()
            if clean:
                elements.append(Paragraph(clean, body_style))
                elements.append(Spacer(1, 2 * mm))

        # ── AI Insights ──
        elements.append(Paragraph("AI-Generated Insights", heading_style))
        for idx, insight in enumerate(insights, 1):
            elements.append(Paragraph(
                f"<b>{idx}.</b> {insight}", bullet_style
            ))

        # ── Recommendations ──
        elements.append(Paragraph("Recommendations", heading_style))
        for idx, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(
                f"<b>{idx}.</b> {rec}", bullet_style
            ))

        # ── Footer ──
        elements.append(Spacer(1, 12 * mm))
        elements.append(HRFlowable(
            width="100%", thickness=0.5, color=BORDER_GREY,
            spaceBefore=4, spaceAfter=4,
        ))
        elements.append(Paragraph(
            f"Generated by TwinEngine Hospitality AI &nbsp;|&nbsp; "
            f"{timezone.now().strftime('%d %b %Y, %I:%M %p')} &nbsp;|&nbsp; "
            f"Powered by Azure GPT-4o",
            footer_style,
        ))

        doc.build(elements)
        return buffer.getvalue()


class DailyReportView(APIView):
    """
    API endpoint to retrieve AI-generated operational summary.
    
    GET /api/reports/daily/?date=YYYY-MM-DD&outlet=<id>
    Response: { report_text, insights, recommendations, cloudinary_url }
    """
    
    @extend_schema(
        tags=['Reports'],
        summary='Get latest AI report for a date',
        parameters=[
            OpenApiParameter('date', OpenApiTypes.DATE, description='Report date (YYYY-MM-DD, default today)'),
            OpenApiParameter('outlet', OpenApiTypes.INT, description='Outlet ID'),
        ],
        responses={200: DailyReportResponseSerializer, 404: None},
    )
    def get(self, request):
        date_str = request.query_params.get('date')
        outlet_id = request.query_params.get('outlet')
        
        if not date_str:
            date_str = timezone.now().date().isoformat()
        
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find existing completed report
        qs = PDFReport.objects.filter(
            start_date__lte=report_date,
            end_date__gte=report_date,
            status='COMPLETED'
        )
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        report = qs.order_by('-completed_at').first()
        
        if report:
            return Response({
                'report_id': report.pk,
                'report_text': report.gpt_summary,
                'insights': report.insights,
                'recommendations': report.recommendations,
                'generated_at': report.completed_at,
                'generated_by': report.generated_by,
                'cloudinary_url': report.cloudinary_url or None,
            })
        else:
            return Response(
                {
                    'error': f'No report found for date {report_date}. '
                             f'Use POST /api/reports/generate/ to create one.',
                    'hint': {
                        'url': '/api/reports/generate/',
                        'method': 'POST',
                        'body': {
                            'outlet_id': outlet_id or '<outlet_id>',
                            'report_type': 'DAILY',
                            'start_date': str(report_date),
                        }
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )


class GenerateDataView(APIView):
    """
    Generate realistic synthetic data for an outlet.
    Populates all database tables: tables, orders, payments,
    inventory, staff schedules, sales data, and daily summaries.

    POST /api/generate-data/
    Body: { "outlet_id": 1, "date": "2026-03-06", "order_count": 40 }
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Data Generation'],
        summary='Generate synthetic restaurant data for an outlet',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'outlet_id': {'type': 'integer', 'description': 'Outlet ID'},
                    'date': {'type': 'string', 'format': 'date', 'description': 'End date of the range (YYYY-MM-DD)'},
                    'order_count': {'type': 'integer', 'description': 'Base orders per day (default 40)'},
                    'days': {'type': 'integer', 'description': 'Number of days of history to generate (default 14)'},
                },
                'required': ['outlet_id'],
            }
        },
        responses={200: {'type': 'object'}},
    )
    def post(self, request):
        from apps.hospitality_group.models import Outlet
        from .data_generator import generate_outlet_data

        # Validate user is a manager
        if not request.user.is_superuser:
            if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER':
                return Response(
                    {'error': 'Only managers can generate data.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        outlet_id = request.data.get('outlet_id')
        if not outlet_id:
            return Response(
                {'error': 'outlet_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            outlet = Outlet.objects.get(pk=outlet_id)
        except Outlet.DoesNotExist:
            return Response(
                {'error': f'Outlet {outlet_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Parse optional date
        target_date = None
        date_str = request.data.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        order_count = request.data.get('order_count', 40)
        try:
            order_count = int(order_count)
            if order_count < 1 or order_count > 200:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'order_count must be an integer between 1 and 200.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        days = request.data.get('days', 14)
        try:
            days = int(days)
            if days < 1 or days > 30:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'days must be an integer between 1 and 30.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            results = generate_outlet_data(outlet_id, target_date, order_count, days)
        except Exception as e:
            logger.exception("Data generation failed")
            return Response(
                {'error': f'Data generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'message': f'Data generated successfully for {outlet.name}',
            'outlet_id': outlet.id,
            'outlet_name': outlet.name,
            'date': str(target_date or timezone.now().date()),
            'created': results,
        })
