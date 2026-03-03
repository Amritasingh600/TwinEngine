"""
Management command to train all ML models for an outlet.
Usage:
    python manage.py train_models --outlet 4
    python manage.py train_models --all
"""
from django.core.management.base import BaseCommand
from apps.predictive_core.ml.prediction_service import PredictionService
from apps.hospitality_group.models import Outlet


class Command(BaseCommand):
    help = "Train all ML prediction models for one or all outlets"

    def add_arguments(self, parser):
        parser.add_argument('--outlet', type=int, help='Outlet ID to train for')
        parser.add_argument('--all', action='store_true', help='Train for all outlets')

    def handle(self, *args, **options):
        service = PredictionService()

        if options['all']:
            outlets = Outlet.objects.all()
        elif options['outlet']:
            outlets = Outlet.objects.filter(id=options['outlet'])
        else:
            self.stderr.write(self.style.ERROR("Provide --outlet <id> or --all"))
            return

        for outlet in outlets:
            self.stdout.write("")
            self.stdout.write("=" * 60)
            self.stdout.write("Training models for: {} (ID: {})".format(outlet.name, outlet.pk))
            self.stdout.write("=" * 60)

            results = service.train_all(outlet.pk)

            for model_name, result in results.items():
                status_str = result.get('status', 'unknown')
                if status_str == 'trained':
                    metrics = result.get('metrics', {})
                    self.stdout.write(self.style.SUCCESS(
                        "  [OK] {}: MAE={}, R2={}, samples={}".format(
                            model_name,
                            metrics.get('mae'),
                            metrics.get('r2'),
                            metrics.get('train_samples', metrics.get('categories', '-')),
                        )
                    ))
                elif status_str == 'skipped':
                    self.stdout.write(self.style.WARNING(
                        "  [SKIP] {}: {}".format(model_name, result.get('reason'))
                    ))
                elif 'rule-based' in status_str:
                    self.stdout.write(
                        "  [RULE] {}: {}".format(model_name, status_str)
                    )
                else:
                    self.stdout.write(self.style.ERROR(
                        "  [ERR] {}: {}".format(model_name, result.get('error', status_str))
                    ))

        self.stdout.write(self.style.SUCCESS("\nDone."))
