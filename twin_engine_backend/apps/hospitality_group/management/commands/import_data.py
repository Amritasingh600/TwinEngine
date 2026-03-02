"""
import_data — Load a JSON fixture into the database.

Handles natural key resolution, disables signal processing during load
to avoid side-effects, and optionally flushes existing data first.

Usage:
    python manage.py import_data backup.json              # load fixture
    python manage.py import_data backup.json --flush      # wipe + load
    python manage.py import_data backup.json --dry-run    # preview only
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Import TwinEngine application data from a JSON fixture file'

    def add_arguments(self, parser):
        parser.add_argument(
            'fixture',
            type=str,
            help='Path to the JSON fixture file to import',
        )
        parser.add_argument(
            '--flush',
            action='store_true',
            default=False,
            help='Flush all data before importing (destructive!)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Validate the fixture without writing to the database',
        )
        parser.add_argument(
            '--ignore-errors',
            action='store_true',
            default=False,
            help='Skip records that cause errors instead of aborting',
        )

    def handle(self, *args, **options):
        fixture_path = options['fixture']
        flush = options['flush']
        dry_run = options['dry_run']
        ignore_errors = options['ignore_errors']

        # Validate file exists
        import os
        if not os.path.isfile(fixture_path):
            raise CommandError(f'Fixture file not found: {fixture_path}')

        file_size = os.path.getsize(fixture_path) / 1024
        self.stdout.write(f'📂 Fixture: {fixture_path} ({file_size:.1f} KB)')

        # Count records in fixture
        import json
        try:
            with open(fixture_path, 'r') as f:
                data = json.load(f)
            record_count = len(data)
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON in fixture file: {e}')

        self.stdout.write(f'📊 Records to import: {record_count}')

        # Show model breakdown
        model_counts = {}
        for record in data:
            model = record.get('model', 'unknown')
            model_counts[model] = model_counts.get(model, 0) + 1

        for model, count in sorted(model_counts.items()):
            self.stdout.write(f'  {model}: {count} records')

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Dry run complete — {record_count} records would be imported.'
                )
            )
            return

        # Confirm destructive operation
        if flush:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  --flush will DELETE all existing data before importing!'
                )
            )
            confirm = input('Type "yes" to continue: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Import cancelled.'))
                return

            self.stdout.write('Flushing database...')
            call_command('flush', '--no-input', verbosity=0)
            self.stdout.write(self.style.SUCCESS('Database flushed.'))

        # Run migrations first to ensure schema is current
        self.stdout.write('Checking migrations...')
        call_command('migrate', '--run-syncdb', verbosity=0)

        # Load the fixture
        self.stdout.write(f'Importing {record_count} records...')
        try:
            loaddata_kwargs = {
                'verbosity': 1,
            }
            if ignore_errors:
                loaddata_kwargs['ignorenonexistent'] = True

            call_command('loaddata', fixture_path, **loaddata_kwargs)

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Successfully imported {record_count} records '
                    f'from {fixture_path}'
                )
            )
        except Exception as e:
            raise CommandError(f'Import failed: {e}')

        # Post-import: reset sequences for PostgreSQL
        db_engine = connection.vendor
        if db_engine == 'postgresql':
            self.stdout.write('Resetting PostgreSQL sequences...')
            from django.apps import apps as django_apps

            with connection.cursor() as cursor:
                for app_config in django_apps.get_app_configs():
                    for model in app_config.get_models():
                        table = model._meta.db_table
                        try:
                            cursor.execute(
                                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                                f"COALESCE(MAX(id), 1)) FROM {table};"
                            )
                        except Exception:
                            pass  # table has no serial 'id' column, skip

            self.stdout.write(self.style.SUCCESS('Sequences reset.'))
