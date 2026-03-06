"""
Quick management command to test Mailtrap email delivery.

Usage:
    python manage.py test_email
    python manage.py test_email --to someone@example.com
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = "Send a test email via the configured SMTP backend (Mailtrap)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            default='test@twinengine.io',
            help='Recipient email address (default: test@twinengine.io)',
        )

    def handle(self, *args, **options):
        recipient = options['to']

        self.stdout.write(f"SMTP config:")
        self.stdout.write(f"  EMAIL_BACKEND = {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  EMAIL_HOST    = {settings.EMAIL_HOST}")
        self.stdout.write(f"  EMAIL_PORT    = {settings.EMAIL_PORT}")
        self.stdout.write(f"  EMAIL_USE_TLS = {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"  EMAIL_USE_SSL = {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"  EMAIL_HOST_USER = {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"  FROM          = {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"  TO            = {recipient}")
        self.stdout.write("")

        try:
            count = send_mail(
                subject='[TwinEngine] Test Email ✅',
                message='If you see this in your Mailtrap inbox, email delivery is working!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                html_message=(
                    '<div style="font-family:sans-serif;padding:24px;">'
                    '<h2 style="color:#2980b9;">TwinEngine Test Email ✅</h2>'
                    '<p>If you see this in your <strong>Mailtrap inbox</strong>, '
                    'email delivery is working correctly.</p>'
                    '<hr><p style="color:#95a5a6;font-size:12px;">'
                    'Sent by <code>python manage.py test_email</code></p></div>'
                ),
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(
                f"✅ Mailtrap email sent! (send_mail returned {count})"
            ))
            self.stdout.write(self.style.SUCCESS(
                "Check your Mailtrap inbox at https://mailtrap.io/inboxes"
            ))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"❌ Mailtrap email failed: {exc}"))

        # ── Gmail copy ──
        gmail_email = getattr(settings, 'GMAIL_EMAIL', '')
        gmail_password = getattr(settings, 'GMAIL_APP_PASSWORD', '')
        if gmail_email and gmail_password:
            self.stdout.write(f"\nGmail config:")
            self.stdout.write(f"  GMAIL_EMAIL = {gmail_email}")
            try:
                import smtplib, ssl
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                msg = MIMEMultipart('alternative')
                msg['Subject'] = '[TwinEngine] Test Email ✅ (Gmail)'
                msg['From'] = gmail_email
                msg['To'] = gmail_email
                msg.attach(MIMEText('Gmail delivery is working!', 'plain'))
                msg.attach(MIMEText(
                    '<div style="font-family:sans-serif;padding:24px;">'
                    '<h2 style="color:#2980b9;">TwinEngine Test Email ✅ (Gmail)</h2>'
                    '<p>Gmail dual delivery is working correctly.</p></div>',
                    'html',
                ))
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ctx) as srv:
                    srv.login(gmail_email, gmail_password)
                    srv.sendmail(gmail_email, gmail_email, msg.as_string())
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Gmail email sent to {gmail_email}!"
                ))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"❌ Gmail failed: {exc}"))
        else:
            self.stdout.write("\n⚠️  Gmail not configured (GMAIL_EMAIL / GMAIL_APP_PASSWORD missing).")
