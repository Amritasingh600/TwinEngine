"""
export_data — Dump all TwinEngine app data to a JSON fixture file.

Excludes Django internal tables (content types, permissions, sessions) to
avoid conflicts when loading into a fresh database.

Usage:
    python manage.py export_data                          # → backup.json
    python manage.py export_data -o my_backup.json        # custom filename
    python manage.py export_data --indent 4               # pretty-print
    python manage.py export_data --apps order_engine      # single app only
"""

import os
import json
from datetime import datetime

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers import serialize


# Apps whose data we export (local + third-party we own)
LOCAL_APPS = [
    'hospitality_group',
    'layout_twin',
    'order_engine',
    'predictive_core',
    'insights_hub',
]

# Django models to always skip (cause PK conflicts on import)
EXCLUDED_MODELS = {
    'contenttypes.contenttype',
    'auth.permission',
    'sessions.session',
    'admin.logentry',
}


class Command(BaseCommand):
    help = 'Export all TwinEngine application data to a JSON fixture file'

    def add_arguments(self, parser):
        parser.add_argument(
            '-o', '--output',
            type=str,
            default=None,
            help='Output file path (default: backup_YYYYMMDD_HHMMSS.json)',
        )
        parser.add_argument(
            '--indent',
            type=int,
            default=2,
            help='JSON indentation level (default: 2)',
        )
        parser.add_argument(
            '--apps',
            nargs='*',
            default=None,
            help='Specific app labels to export (default: all local apps)',
        )
        parser.add_argument(
            '--include-auth',
            action='store_true',
            default=False,
            help='Include auth.User and auth.Group data',
        )

    def handle(self, *args, **options):
        target_apps = options['apps'] or LOCAL_APPS
        include_auth = options['include_auth']
        indent = options['indent']

        # Build output filename
        if options['output']:
            output_path = options['output']
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'backup_{timestamp}.json'

        # Resolve models to serialize
        models_to_export = []

        if include_auth:
            try:
                models_to_export.append(apps.get_model('auth', 'Group'))
                models_to_export.append(apps.get_model('auth', 'User'))
            except LookupError:
                pass

        for app_label in target_apps:
            # Normalise: allow both 'order_engine' and 'apps.order_engine'
            clean_label = app_label.replace('apps.', '')
            full_label = f'apps.{clean_label}'

            try:
                app_config = apps.get_app_config(full_label)
            except LookupError:
                try:
                    app_config = apps.get_app_config(clean_label)
                except LookupError:
                    self.stderr.write(
                        self.style.WARNING(f'App "{app_label}" not found, skipping.')
                    )
                    continue

            for model in app_config.get_models():
                model_key = f'{model._meta.app_label}.{model._meta.model_name}'
                if model_key not in EXCLUDED_MODELS:
                    models_to_export.append(model)

        if not models_to_export:
            raise CommandError('No models found to export.')

        # Serialize
        all_objects = []
        total_count = 0

        for model in models_to_export:
            model_label = f'{model._meta.app_label}.{model._meta.model_name}'
            queryset = model.objects.all()
            count = queryset.count()

            if count > 0:
                serialized = serialize('python', queryset)
                all_objects.extend(serialized)
                total_count += count
                self.stdout.write(f'  {model_label}: {count} records')
            else:
                self.stdout.write(
                    self.style.WARNING(f'  {model_label}: 0 records (skipped)')
                )

        # Write JSON
        json_data = json.loads(serialize('json', []))  # start fresh
        # Re-serialize using the collected python objects
        json_output = serialize('json', sum(
            [list(model.objects.all()) for model in models_to_export if model.objects.exists()],
            []
        ), indent=indent)

        with open(output_path, 'w') as f:
            f.write(json_output)

        file_size = os.path.getsize(output_path)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Exported {total_count} records to {output_path} '
                f'({file_size / 1024:.1f} KB)'
            )
        )
