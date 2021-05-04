from django.apps import AppConfig


class ComplianceBinderConfig(AppConfig):
    name = 'compliance_binder'
    verbose_name = "Compliance Binder"

    def ready(self):
        from . import signal_handlers
