from django.apps import AppConfig


class BrandConfig(AppConfig):
    name = 'brand'
    verbose_name = "Organization"

    def ready(self):
        from . import signal_handlers
