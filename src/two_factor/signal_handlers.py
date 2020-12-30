from django.apps import apps
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver

from authy.api import AuthyApiClient

from .conf import settings

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)


AuthyOneTouchDevice = apps.get_model('two_factor', 'AuthyOneTouchDevice')
AuthySoftTOTPDevice = apps.get_model('two_factor', 'AuthySoftTOTPDevice')
AuthyUser = apps.get_model('two_factor', 'AuthyUser')


@receiver(signals.post_delete, sender=AuthyOneTouchDevice)
@receiver(signals.post_delete, sender=AuthySoftTOTPDevice)
def post_delete_authy_device(sender, instance, **kwargs):
    if sender == AuthyOneTouchDevice:
        qs = AuthySoftTOTPDevice.objects.all()
    elif sender == AuthySoftTOTPDevice:
        qs = AuthyOneTouchDevice.objects.all()
    if qs:
        qs.filter(user=instance.user, authy_user=instance.authy_user).delete()

    if not AuthyOneTouchDevice.objects.filter(authy_user=instance.authy_user):
        if not AuthySoftTOTPDevice.objects.filter(authy_user=instance.authy_user):
            instance.authy_user.delete()

@receiver(signals.post_save, sender=AuthyOneTouchDevice)
def post_save_authy_one_touch_device(sender, instance, created, **kwargs):
    if created:
        try:
            device = AuthySoftTOTPDevice.objects.get(user=instance.user)
        except AuthySoftTOTPDevice.DoesNotExist:
            pass
        else:
            device.delete()
        device = AuthySoftTOTPDevice.objects.create(
            user=instance.user,
            authy_user=instance.authy_user,
            confirmed=instance.confirmed,
        )

@receiver(signals.post_delete, sender=AuthyUser)
def pre_delete_authy_user(sender, instance, **kwargs):
    deleted = authy_api.users.delete(instance.authy_id)
    if deleted.ok():
        print(deleted.content)
