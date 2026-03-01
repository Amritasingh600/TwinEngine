from django.apps import AppConfig


class OrderEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.order_engine'
    verbose_name = 'Order Engine'

    def ready(self):
        """
        Import signals when app is ready.
        This ensures signal handlers are connected when Django starts.
        """
        import apps.order_engine.signals  # noqa: F401
