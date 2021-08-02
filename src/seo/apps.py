from django.apps import AppConfig


class SeoConfig(AppConfig):
    name = 'seo'

    def ready(self):
        from . import signal_handlers
