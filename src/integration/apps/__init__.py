from django.apps import AppConfig


class IntegrationConfig(AppConfig):
    name = 'integration'

    def ready(self):
        from ..box_sign_event_tracker import start_tracking
        start_tracking()