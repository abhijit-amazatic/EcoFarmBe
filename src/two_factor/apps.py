from django.apps import AppConfig


class TwoFactorConfig(AppConfig):
    name = 'two_factor'

    def ready(self):
        from . import signal_handlers
