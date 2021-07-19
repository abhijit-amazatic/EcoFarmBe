from django.apps import AppConfig, apps
from django.db.models import signals
from reversion.signals import (pre_revision_commit, post_revision_commit)

from reversion.revisions import is_active, register, is_registered, set_comment, create_revision, set_user
from reversion_compare.helpers import patch_admin
from django.contrib.admin import site as admin_site

from .config import tracking_app_models


class ReversionExtentionConfig(AppConfig):
    name = 'reversion_extention'

    def ready(self):
        from .admin import VersionAdmin
        from . import signal_handlers
        for app_label, model_names in tracking_app_models.items():
            for model_name in model_names:
                model = apps.get_model(app_label=app_label, model_name=model_name)
                if model in admin_site._registry:
                    patch_admin(model, AdminClass=VersionAdmin)
                
                self.register_reversion(model)
                signals.pre_save.connect(signal_handlers.pre_save_handler, sender=model)
                signals.post_save.connect(signal_handlers.post_save_handler, sender=model)
                signals.post_delete.connect(signal_handlers.post_delete_handler, sender=model)
        post_revision_commit.connect(signal_handlers.post_revision_commit_handler)

    def register_reversion(self, model, follow=()):
        if not is_registered(model):
            for parent_model, field in model._meta.concrete_model._meta.parents.items():
                follow += (field.name,)
                self.register_reversion(parent_model, ())
            register(model, follow=follow)
