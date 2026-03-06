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
                f"✅ Email sent successfully! (send_mail returned {count})"
            ))
            self.stdout.write(self.style.SUCCESS(
                "Check your Mailtrap inbox at https://mailtrap.io/inboxes"
            ))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"❌ Email failed: {exc}"))
