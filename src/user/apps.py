from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'user'

    def ready(self):
        from . import signal_handlers
