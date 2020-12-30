from django.apps import AppConfig


class BrandConfig(AppConfig):
    name = 'brand'

    def ready(self):
        from . import signal_handlers
