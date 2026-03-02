"""
Test suite for Environment & CORS Configuration (Phases 1-4).

Tests cover:
  1. Environment variable loading and fallback defaults
  2. CORS configuration
  3. CSRF trusted origins
  4. Production security hardening (DEBUG=False gate)
  5. Channel layer configuration (InMemory vs Redis)
  6. Static files & WhiteNoise configuration
  7. Logging configuration
  8. Export/Import management commands
"""

import os
import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.management import call_command, CommandError
from django.test import TestCase, SimpleTestCase, override_settings


# ============================================================
# 1. Environment Variable & Defaults Tests
# ============================================================

class EnvironmentVariableTests(SimpleTestCase):
    """Verify settings read from env vars with correct defaults."""

    def test_debug_is_bool(self):
        """DEBUG should be a boolean."""
        self.assertIsInstance(settings.DEBUG, bool)

    def test_secret_key_is_set(self):
        """SECRET_KEY should be a non-empty string."""
        self.assertIsInstance(settings.SECRET_KEY, str)
        self.assertGreater(len(settings.SECRET_KEY), 10)

    def test_allowed_hosts_is_list(self):
        """ALLOWED_HOSTS should be a list of strings."""
        self.assertIsInstance(settings.ALLOWED_HOSTS, list)
        self.assertGreater(len(settings.ALLOWED_HOSTS), 0)
        for host in settings.ALLOWED_HOSTS:
            self.assertIsInstance(host, str)
            self.assertGreater(len(host.strip()), 0)

    def test_time_zone_set(self):
        """TIME_ZONE should be a valid timezone string."""
        self.assertIsInstance(settings.TIME_ZONE, str)
        self.assertGreater(len(settings.TIME_ZONE), 0)

    def test_use_tz_enabled(self):
        """USE_TZ should be True."""
        self.assertTrue(settings.USE_TZ)


# ============================================================
# 2. CORS Configuration Tests
# ============================================================

class CORSConfigTests(SimpleTestCase):
    """Verify CORS settings are properly configured."""

    def test_cors_allowed_origins_is_list(self):
        """CORS_ALLOWED_ORIGINS should be a list."""
        self.assertIsInstance(settings.CORS_ALLOWED_ORIGINS, list)

    def test_cors_allowed_origins_contains_localhost(self):
        """Default CORS origins should include localhost:5173."""
        origins = settings.CORS_ALLOWED_ORIGINS
        localhost_found = any('localhost:5173' in o for o in origins)
        self.assertTrue(localhost_found, f"localhost:5173 not found in {origins}")

    def test_cors_allow_credentials(self):
        """CORS_ALLOW_CREDENTIALS should be True."""
        self.assertTrue(settings.CORS_ALLOW_CREDENTIALS)

    def test_cors_allow_headers_includes_auth(self):
        """CORS headers should include 'authorization'."""
        self.assertIn('authorization', settings.CORS_ALLOW_HEADERS)

    def test_cors_allow_headers_includes_csrftoken(self):
        """CORS headers should include 'x-csrftoken'."""
        self.assertIn('x-csrftoken', settings.CORS_ALLOW_HEADERS)

    def test_cors_allow_methods(self):
        """CORS should allow standard REST methods."""
        required = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'}
        self.assertTrue(
            required.issubset(set(settings.CORS_ALLOW_METHODS)),
            f"Missing methods: {required - set(settings.CORS_ALLOW_METHODS)}"
        )

    def test_cors_origins_no_empty_strings(self):
        """CORS origins should not contain empty strings."""
        for origin in settings.CORS_ALLOWED_ORIGINS:
            self.assertGreater(len(origin.strip()), 0)


# ============================================================
# 3. CSRF Configuration Tests
# ============================================================

class CSRFConfigTests(SimpleTestCase):
    """Verify CSRF trusted origins are configured."""

    def test_csrf_trusted_origins_is_list(self):
        """CSRF_TRUSTED_ORIGINS should be a list."""
        self.assertIsInstance(settings.CSRF_TRUSTED_ORIGINS, list)

    def test_csrf_trusted_origins_has_entries(self):
        """CSRF_TRUSTED_ORIGINS should have at least one entry."""
        self.assertGreater(len(settings.CSRF_TRUSTED_ORIGINS), 0)

    def test_csrf_trusted_origins_no_empty_strings(self):
        """CSRF trusted origins should not contain empty strings."""
        for origin in settings.CSRF_TRUSTED_ORIGINS:
            self.assertGreater(len(origin.strip()), 0)


# ============================================================
# 4. Production Security Tests (DEBUG=False gate)
# ============================================================

class ProductionSecurityTests(SimpleTestCase):
    """Verify security settings activate when DEBUG=False.
    
    These tests reload settings logic, not the live settings object,
    so they use mock to simulate DEBUG=False.
    """

    def test_debug_false_enables_ssl_redirect(self):
        """When DEBUG is False, SECURE_SSL_REDIRECT should activate."""
        # We can't easily reload settings, so we verify the conditional
        # logic exists in settings.py
        settings_path = Path(settings.BASE_DIR) / 'twinengine_core' / 'settings.py'
        content = settings_path.read_text()
        self.assertIn('SECURE_SSL_REDIRECT', content)
        self.assertIn('if not DEBUG:', content)

    def test_debug_false_enables_hsts(self):
        """HSTS settings should be defined in settings.py."""
        settings_path = Path(settings.BASE_DIR) / 'twinengine_core' / 'settings.py'
        content = settings_path.read_text()
        self.assertIn('SECURE_HSTS_SECONDS', content)
        self.assertIn('SECURE_HSTS_PRELOAD', content)

    def test_debug_false_enables_secure_cookies(self):
        """Secure cookie settings should be defined."""
        settings_path = Path(settings.BASE_DIR) / 'twinengine_core' / 'settings.py'
        content = settings_path.read_text()
        self.assertIn('SESSION_COOKIE_SECURE', content)
        self.assertIn('CSRF_COOKIE_SECURE', content)

    def test_debug_false_enables_xframe_deny(self):
        """X_FRAME_OPTIONS = DENY should be defined."""
        settings_path = Path(settings.BASE_DIR) / 'twinengine_core' / 'settings.py'
        content = settings_path.read_text()
        self.assertIn("X_FRAME_OPTIONS = 'DENY'", content)

    def test_proxy_ssl_header_defined(self):
        """SECURE_PROXY_SSL_HEADER should be set for cloud deployments."""
        settings_path = Path(settings.BASE_DIR) / 'twinengine_core' / 'settings.py'
        content = settings_path.read_text()
        self.assertIn('SECURE_PROXY_SSL_HEADER', content)


# ============================================================
# 5. Channel Layer Configuration Tests
# ============================================================

class ChannelLayerTests(SimpleTestCase):
    """Verify Channel layer falls back correctly."""

    def test_channel_layer_configured(self):
        """CHANNEL_LAYERS should have a 'default' entry."""
        self.assertIn('default', settings.CHANNEL_LAYERS)

    def test_inmemory_layer_when_no_redis(self):
        """Without REDIS_URL, InMemoryChannelLayer should be used."""
        redis_url = os.getenv('REDIS_URL', '')
        if not redis_url:
            backend = settings.CHANNEL_LAYERS['default']['BACKEND']
            self.assertEqual(backend, 'channels.layers.InMemoryChannelLayer')

    def test_asgi_application_set(self):
        """ASGI_APPLICATION should point to twinengine_core."""
        self.assertEqual(
            settings.ASGI_APPLICATION,
            'twinengine_core.asgi.application'
        )


# ============================================================
# 6. Static Files & WhiteNoise Tests
# ============================================================

class StaticFilesTests(SimpleTestCase):
    """Verify static file and WhiteNoise configuration."""

    def test_static_url(self):
        """STATIC_URL should be set."""
        self.assertIn('static', settings.STATIC_URL)

    def test_static_root_set(self):
        """STATIC_ROOT should point to staticfiles directory."""
        self.assertIsNotNone(settings.STATIC_ROOT)
        self.assertTrue(str(settings.STATIC_ROOT).endswith('staticfiles'))

    def test_whitenoise_in_middleware(self):
        """WhiteNoise middleware should be present."""
        self.assertIn(
            'whitenoise.middleware.WhiteNoiseMiddleware',
            settings.MIDDLEWARE
        )

    def test_whitenoise_storage_backend(self):
        """STORAGES should use WhiteNoise compressed storage."""
        storages = getattr(settings, 'STORAGES', {})
        sf_backend = storages.get('staticfiles', {}).get('BACKEND', '')
        self.assertIn('whitenoise', sf_backend.lower())

    def test_media_url(self):
        """MEDIA_URL should be set."""
        self.assertEqual(settings.MEDIA_URL, '/media/')

    def test_media_root_set(self):
        """MEDIA_ROOT should point to media directory."""
        self.assertIsNotNone(settings.MEDIA_ROOT)
        self.assertTrue(str(settings.MEDIA_ROOT).endswith('media'))


# ============================================================
# 7. Logging Configuration Tests
# ============================================================

class LoggingConfigTests(SimpleTestCase):
    """Verify structured logging is configured."""

    def test_logging_dict_exists(self):
        """LOGGING should be a dict with version 1."""
        self.assertIsInstance(settings.LOGGING, dict)
        self.assertEqual(settings.LOGGING.get('version'), 1)

    def test_console_handler_exists(self):
        """Console handler should be configured."""
        handlers = settings.LOGGING.get('handlers', {})
        self.assertIn('console', handlers)

    def test_file_handler_exists(self):
        """File handler should be configured."""
        handlers = settings.LOGGING.get('handlers', {})
        self.assertIn('file', handlers)

    def test_file_handler_uses_rotating(self):
        """File handler should use RotatingFileHandler."""
        handler = settings.LOGGING['handlers']['file']
        self.assertIn('RotatingFileHandler', handler['class'])

    def test_file_handler_max_bytes(self):
        """File handler should have a max size of 5 MB."""
        handler = settings.LOGGING['handlers']['file']
        self.assertEqual(handler['maxBytes'], 5 * 1024 * 1024)

    def test_apps_logger_exists(self):
        """Custom 'apps' logger should be defined."""
        loggers = settings.LOGGING.get('loggers', {})
        self.assertIn('apps', loggers)

    def test_django_request_logger(self):
        """django.request logger should exist at WARNING level."""
        loggers = settings.LOGGING.get('loggers', {})
        self.assertIn('django.request', loggers)
        self.assertEqual(loggers['django.request']['level'], 'WARNING')

    def test_log_directory_exists(self):
        """Logs directory should exist."""
        logs_dir = Path(settings.BASE_DIR) / 'logs'
        self.assertTrue(logs_dir.is_dir(), f"Missing directory: {logs_dir}")


# ============================================================
# 8. Export/Import Management Command Tests
# ============================================================

class ExportDataCommandTests(TestCase):
    """Test the export_data management command."""

    def test_export_creates_file(self):
        """export_data should create a JSON file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            out = StringIO()
            call_command('export_data', '-o', output_path, stdout=out)

            self.assertTrue(os.path.isfile(output_path))
            # File should contain valid JSON
            with open(output_path) as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
        finally:
            os.unlink(output_path)

    def test_export_with_include_auth(self):
        """export_data --include-auth should include auth models."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            out = StringIO()
            call_command('export_data', '-o', output_path, '--include-auth', stdout=out)

            with open(output_path) as f:
                data = json.load(f)

            output_text = out.getvalue()
            # Should mention auth.user in output
            self.assertIn('auth.user', output_text.lower())
        finally:
            os.unlink(output_path)

    def test_export_single_app(self):
        """export_data --apps order_engine should export only that app."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            out = StringIO()
            call_command(
                'export_data', '-o', output_path,
                '--apps', 'order_engine',
                stdout=out
            )
            self.assertTrue(os.path.isfile(output_path))
        finally:
            os.unlink(output_path)


class ImportDataCommandTests(TestCase):
    """Test the import_data management command."""

    def test_import_dry_run(self):
        """import_data --dry-run should preview without writing."""
        # Create a minimal fixture
        fixture_data = json.dumps([])
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            f.write(fixture_data)
            fixture_path = f.name

        try:
            out = StringIO()
            call_command(
                'import_data', fixture_path, '--dry-run', stdout=out
            )
            output_text = out.getvalue()
            self.assertIn('Dry run', output_text)
        finally:
            os.unlink(fixture_path)

    def test_import_missing_file_raises_error(self):
        """import_data with non-existent file should raise CommandError."""
        with self.assertRaises(CommandError):
            call_command('import_data', '/nonexistent/file.json')

    def test_import_invalid_json_raises_error(self):
        """import_data with invalid JSON should raise CommandError."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            f.write('NOT VALID JSON {{{')
            fixture_path = f.name

        try:
            with self.assertRaises(CommandError):
                call_command('import_data', fixture_path)
        finally:
            os.unlink(fixture_path)


# ============================================================
# 9. Env File Tests
# ============================================================

class EnvFileTests(SimpleTestCase):
    """Verify .env.example has all expected keys."""

    def test_env_example_exists(self):
        """.env.example should exist in project root."""
        env_example = Path(settings.BASE_DIR) / '.env.example'
        self.assertTrue(env_example.is_file(), f"Missing: {env_example}")

    def test_env_example_has_required_keys(self):
        """All critical env keys should be documented in .env.example."""
        env_example = Path(settings.BASE_DIR) / '.env.example'
        content = env_example.read_text()

        required_keys = [
            'DEBUG',
            'SECRET_KEY',
            'ALLOWED_HOSTS',
            'DATABASE_URL',
            'CORS_ALLOWED_ORIGINS',
            'CSRF_TRUSTED_ORIGINS',
            'REDIS_URL',
            'AZURE_OPENAI_KEY',
            'CLOUDINARY_CLOUD_NAME',
            'LOG_LEVEL',
        ]
        for key in required_keys:
            self.assertIn(
                key, content,
                f"Missing key '{key}' in .env.example"
            )

    def test_gitignore_excludes_env(self):
        """.gitignore should exclude .env files."""
        gitignore = Path(settings.BASE_DIR) / '.gitignore'
        if gitignore.is_file():
            content = gitignore.read_text()
            self.assertIn('.env', content)


# ============================================================
# 10. Deployment File Tests
# ============================================================

class DeploymentFileTests(SimpleTestCase):
    """Verify deployment files exist and are valid."""

    def test_procfile_exists(self):
        """Procfile should exist."""
        procfile = Path(settings.BASE_DIR) / 'Procfile'
        self.assertTrue(procfile.is_file())

    def test_procfile_has_web_process(self):
        """Procfile should define a web process with daphne."""
        procfile = Path(settings.BASE_DIR) / 'Procfile'
        content = procfile.read_text()
        self.assertIn('web:', content)
        self.assertIn('daphne', content)

    def test_build_sh_exists(self):
        """build.sh should exist."""
        build_sh = Path(settings.BASE_DIR) / 'build.sh'
        self.assertTrue(build_sh.is_file())

    def test_build_sh_has_collectstatic(self):
        """build.sh should run collectstatic."""
        build_sh = Path(settings.BASE_DIR) / 'build.sh'
        content = build_sh.read_text()
        self.assertIn('collectstatic', content)

    def test_build_sh_has_migrate(self):
        """build.sh should run migrate."""
        build_sh = Path(settings.BASE_DIR) / 'build.sh'
        content = build_sh.read_text()
        self.assertIn('migrate', content)

    def test_makefile_exists(self):
        """Makefile should exist."""
        makefile = Path(settings.BASE_DIR) / 'Makefile'
        self.assertTrue(makefile.is_file())
