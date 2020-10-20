from base64 import b32encode
from binascii import unhexlify
from datetime import timedelta
from urllib.parse import quote, urlencode
import time
import jwt

from django.contrib.postgres.fields import (JSONField,)
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.core import serializers
from django_otp.models import ThrottlingMixin
from django_otp.oath import (TOTP,)

from authy.api import AuthyApiClient
from phonenumber_field.modelfields import PhoneNumberField
from core.mixins.models import (TimeStampFlagModelMixin, )

from .abstract_models import (AbstractDevice, AbstractPhoneDevice)
from .conf import settings
from .utils import (
    random_hex,
    random_hex_32,
    pk_hex,
    static_token,
    key_validator,
)

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)


class TwoFactorLoginToken(TimeStampFlagModelMixin, models.Model):
    """
    Token to identify user.
    """
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE
    )
    token = models.CharField(
        max_length=128,
        validators=[key_validator],
        default=random_hex_32,
        help_text="A hex-encoded token.",
        db_index=True,
    )
    devices_last_request = JSONField(
        _("Authy Response"),
        default=dict,
        editable=False,
    )

    @property
    def is_valid(self):
        valid_for_sec = getattr(settings, 'LOGIN_TOKEN_VALID_FOR_SEC')
        return timezone.now() < (self.created_on + timedelta(seconds=valid_for_sec))

    class Meta:
        verbose_name = _("User Two Factor Token")
        verbose_name_plural = _("User Two Factor Tokens")


class PhoneTOTPDevice(AbstractPhoneDevice):
    """
    Phone TOTP device
    """
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        related_name='phone_totp_devices',
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
    )
    phone_number = PhoneNumberField(_('Phone'),)

    class Meta(AbstractPhoneDevice.Meta):
        unique_together = ['user', 'phone_number']
        verbose_name = _("Phone Totp Device")
        verbose_name_plural = _("Phone Totp Device")

    def __str__(self):
        return "{0} | ({1})".format(self.phone_number, self.user)


class AuthyAddUserRequest(models.Model):
    user = models.OneToOneField(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        related_name='authy_add_user_request',
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
        unique=True,
    )
    request_id = models.CharField(
        _("Request Id"),
        max_length=128,
        validators=[key_validator],
        default=random_hex_32,
        help_text="A hex-encoded token.",
        db_index=True,
    )
    custom_user_id = models.CharField(
        _("Custom User Id"),
        max_length=128,
        validators=[key_validator],
        default=random_hex_32,
        help_text="A hex-encoded token.",
    )
    issued_at = models.DateTimeField(
        _("Issued At"),
        default=timezone.now
    )
    # status = models.CharField(_("status"), max_length=50)

    is_registered = models.BooleanField(
        default=False,
        help_text="Is user reregistration complete"
    )
    authy_id = models.CharField(
        _("Authy Id"),
        max_length=128,
        default='',
    )

    @property
    def expire_at(self):
        return self.issued_at + timedelta(seconds=600)

    @property
    def is_expired(self):
        return timezone.now() > self.expire_at

    @property
    def status(self):
        if self.is_registered:
            return 'completed'
        else:
            if self.is_expired:
                return 'expired'
            else:
                return 'pending'

    def get_qr_string(self):
        authy_app_id = settings.AUTHY_APP_ID
        authy_app_Name = settings.AUTHY_APP_NAME
        payload = {
            "iss": authy_app_Name,
            "iat": int(self.issued_at.timestamp()),
            "exp": int(self.expire_at.timestamp()),
            "context": {
                "custom_user_id": self.custom_user_id,
                "authy_app_id": str(authy_app_id),
            }
        }
        headers = {
            "alg": "HS256",
            "typ": "JWT",
        }
        key = settings.AUTHY_ACCOUNT_SECURITY_API_KEY
        jwt_token = jwt.encode(
            payload, key, algorithm='HS256', headers=headers)

        return f'authy://account?token={jwt_token.decode("utf-8")}'

    class Meta:
        verbose_name = _("Authy Add User Request")
        verbose_name_plural = _("Authy Add User Requests")


class AuthyUser(models.Model):
    authy_id = models.BigIntegerField(
        _("Authy Id"),
        unique=True
    )
    app_device_name = models.CharField(
        max_length=255,
        default='unknown',
    )

    class Meta:
        verbose_name = _("Authy Add User Request")
        verbose_name_plural = _("Authy Add User Requests")


class AuthyOneTouchDevice(AbstractDevice):
    """
    Authenticator TOTP device
    """
    user = models.OneToOneField(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        related_name='authy_one_touch_device',
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
    )
    authy_user = models.ForeignKey(
        AuthyUser,
        related_name='authy_one_touch_devices',
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        max_length=255,
        default='Authy Push Authentications',
        help_text="The human-readable name of this device.",
    )

    class Meta(AbstractDevice.Meta):
        verbose_name = _("Authy One Touch Device")
        verbose_name_plural = _("Authy One Touch Devices")

    @property
    def type(self):
        return 'one_touch'

    @property
    def app_device_name(self):
        return self.authy_user.app_device_name

    @property
    def challenge_methods(self):
        return []

    def generate_challenge(self, event_code='', msg=None, **kwargs):
        """
        send totp token
        :param str msg: Message to send on phone.
        """
        if not msg:
            msg = 'Verification requested for Thrive Society account.'
        username_field = self.user.__class__.EMAIL_FIELD
        details = {
            'username': getattr(self.user, username_field,),
        }

        hidden_details = {
            'event_code': event_code
        }

        # logos = [
        #     dict(
        #       res='default',
        #       url='https://www.thrive-society.com/static/media/logo.f8a96e86.png',
        #     )
        #     dict(res='low', url='https://www.thrive-society.com/favicon.png')
        # ]
        seconds_to_expire = 120

        authy_response = authy_api.one_touch.send_request(
            self.authy_user.authy_id,
            msg,
            seconds_to_expire=seconds_to_expire,
            details=details,
            hidden_details=hidden_details,
            # logos=logos,
        )

        if authy_response.ok():
            add_user_request = self.one_touch_request_set.create(
                authy_request_uuid=authy_response.get_uuid(),
                authy_onetouch_device=self,
                seconds_to_expire=seconds_to_expire,
            )
            return (True, {'detail': 'Authy Push Authentications request made.', 'request_id': add_user_request.id})
        else:
            return (True, authy_response.errors())

    def verify_token(self, token, event_code='', **kwargs):
        req = self.one_touch_request_set.filter(pk=token).first()
        if req and req.status == 'approved' and req.event_code == event_code:
            return True
        return False

    def request_status(self, request_id, **kwargs):
        req = self.one_touch_request_set.filter(pk=request_id).first()
        if req:
            return req.status
        return 'unknown'


class AuthyOneTouchRequest(models.Model):
    """
    Authenticator TOTP device
    """

    id = models.CharField(
        _("Id"),
        max_length=64,
        primary_key=True,
        default=pk_hex,
        editable=False,
    )
    authy_request_uuid = models.UUIDField(
        editable=False,
        db_index=True,
    )
    authy_onetouch_device = models.ForeignKey(
        AuthyOneTouchDevice,
        related_name='one_touch_request_set',
        help_text="The device that this request belongs to.",
        on_delete=models.CASCADE,
        editable=False,
    )
    event_code = models.CharField(
        _("Event Code"),
        max_length=255,
        default='',
        editable=False,
    )
    status = models.CharField(
        _("Status"),
        max_length=255,
        default='pending',
        editable=False,
    )
    issued_at = models.DateTimeField(
        _("Issued At"),
        default=timezone.now,
        editable=False,
    )
    seconds_to_expire = models.PositiveSmallIntegerField(
        _("Seconds To Expire"),
        editable=False
    )
    authy_response = JSONField(
        _("Authy Response"),
        default=dict,
        editable=False
    )

    class Meta:
        verbose_name = _("Authy One Touch Request")
        verbose_name_plural = _("Authy One Touch Requests")


class AuthySoftTOTPDevice(AbstractDevice):
    """
    Authenticator TOTP device
    """
    user = models.OneToOneField(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        related_name='authy_soft_totp_device',
        on_delete=models.CASCADE,
    )
    authy_user = models.ForeignKey(
        AuthyUser,
        related_name='authy_soft_totp_devices',
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        max_length=255,
        default='Authy Soft Token',
    )

    class Meta(AbstractDevice.Meta):
        verbose_name = _("Authy Soft TOTP Device")
        verbose_name_plural = _("Authy Soft TOTP Devices")

    @property
    def type(self):
        return 'authy_totp'

    @property
    def app_device_name(self):
        return self.authy_user.app_device_name

    @property
    def is_removable(self):
        return False

    def verify_token(self, token, **kwargs):
        verification = authy_api.tokens.verify(self.authy_user.authy_id, token=token)
        if verification.ok():
            return True
        return False



class AuthenticatorTOTPDevice(ThrottlingMixin, AbstractDevice):
    """
    Authenticator TOTP device
    """
    user = models.OneToOneField(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        related_name='authenticator_totp_device',
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
    )
    key = models.CharField(
        max_length=80,
        validators=[key_validator],
        default=random_hex,
        help_text="A hex-encoded secret key of up to 40 bytes."
    )
    step = models.PositiveSmallIntegerField(
        default=30,
        help_text="The time step in seconds."
    )
    t0 = models.BigIntegerField(
        default=0,
        help_text="The Unix time at which to begin counting steps."
    )
    digits = models.PositiveSmallIntegerField(
        choices=[(6, 6), (8, 8)],
        default=6,
        help_text="The number of digits to expect in a token."
    )
    tolerance = models.PositiveSmallIntegerField(
        default=1,
        help_text="The number of time steps in the past or future to allow."
    )
    drift = models.SmallIntegerField(
        default=0,
        help_text="The number of time steps the prover is known to deviate from our clock."
    )
    last_t = models.BigIntegerField(
        default=-1,
        help_text="The t value of the latest verified token. must be at a higher time step."
    )
    name = models.CharField(
        max_length=64,
        default='Authenticator App',
        help_text="The human-readable name of this device.",
    )

    class Meta(AbstractDevice.Meta):
        verbose_name = _("Authenticator TOTP Device")
        verbose_name_plural = _("Authenticator TOTP Devices")

    @property
    def type(self):
        return 'authenticator_app'

    @property
    def challenge_methods(self):
        return []

    @property
    def bin_key(self):
        """
        The secret key as a binary string.
        """
        return unhexlify(self.key.encode())

    def verify_token(self, token, *args, commit=True, **kwargs):
        totp_sync = getattr(settings, 'AUTHENTICATOR_TOTP_SYNC', True)

        verify_allowed, _ = self.verify_is_allowed()
        if not verify_allowed:
            return False

        try:
            token = int(token)
        except Exception:
            verified = False
        else:
            key = self.bin_key

            totp = TOTP(key, self.step, self.t0, self.digits, self.drift)
            totp.time = time.time()

            verified = totp.verify(token, self.tolerance, self.last_t + 1)
            if verified:
                self.last_t = totp.t()
                if totp_sync:
                    self.drift = totp.drift
                if commit:
                    self.throttle_reset(commit=False)
                    self.save()

        if not verified and commit:
            self.throttle_increment(commit=True)

        return verified

    def get_throttle_factor(self):
        return getattr(settings, 'AUTHENTICATOR_TOTP_THROTTLE_FACTOR', 1)

    @property
    def config_url(self):
        """
        A URL for configuring Google Authenticator or similar.
        See https://github.com/google/google-authenticator/wiki/Key-Uri-Format.
        The issuer is taken from :setting:`OTP_TOTP_ISSUER`, if available.
        """
        label = self.user.email
        params = {
            'secret': b32encode(self.bin_key),
            'algorithm': 'SHA1',
            'digits': self.digits,
            'period': self.step,
        }
        urlencoded_params = urlencode(params)

        issuer = getattr(settings, 'AUTHENTICATOR_TOTP_ISSUER', None)
        if callable(issuer):
            issuer = issuer(self)
        if isinstance(issuer, str) and (issuer != ''):
            issuer = issuer.replace(':', '')
            label = '{}:{}'.format(issuer, label)
            # encode issuer as per RFC 3986, not quote_plus
            urlencoded_params += '&issuer={}'.format(quote(issuer))

        url = 'otpauth://totp/{}?{}'.format(quote(label), urlencoded_params)

        return url


class AddAuthenticatorRequest(models.Model):
    user = models.OneToOneField(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        related_name='add_authenticator_request',
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
        unique=True,
    )
    request_id = models.CharField(
        _("Request Id"),
        max_length=128,
        validators=[key_validator],
        default=random_hex_32,
        db_index=True,
    )
    issued_at = models.DateTimeField(
        _("Issued At"),
        default=timezone.now
    )
    is_completed = models.BooleanField(
        default=False,
    )

    # status = models.CharField(_("status"), max_length=50)
    devices_data = JSONField(
        _("Devices Data"),
        default=list,
        editable=False,
    )

    class Meta:
        verbose_name = _("Add Authenticator Request")
        verbose_name_plural = _("Add Authenticator Requests")

    @property
    def expire_at(self):
        return self.issued_at + timedelta(seconds=600)

    @property
    def is_expired(self):
        return timezone.now() > self.expire_at

    @property
    def status(self):
        if self.is_completed:
            return 'completed'
        else:
            if self.is_expired:
                return 'expired'
            else:
                return 'pending'


    def get_device(self):
        deserialize_obj_gen = serializers.deserialize("json", self.devices_data)
        deserialize_obj = next(deserialize_obj_gen, None)
        if deserialize_obj:
            return deserialize_obj.object
        return None

    def save(self, *args, **kwargs):
        if not self.devices_data:
            self.devices_data = serializers.serialize(
                'json',
                [AuthenticatorTOTPDevice(user=self.user)]
            )
        super().save(*args, **kwargs)


class StaticDevice(ThrottlingMixin, AbstractDevice):
    """
    A static token device
    """
    user = models.OneToOneField(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        verbose_name=_('User'),
        related_name='static_device',
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=64,
        default='Backup Code',
        help_text="The human-readable name of this device.",
    )
    confirmed = models.BooleanField(default=True, help_text="Is this device ready for use?")


    class Meta(AbstractDevice.Meta):
        verbose_name = _("Static Backup Code Device")
        verbose_name_plural = _("Static Backup Code Devices")

    @property
    def type(self):
        return 'backup_code'

    @property
    def is_removable(self):
        return False

    @property
    def challenge_methods(self):
        return []

    def get_throttle_factor(self):
        return getattr(settings, 'OTP_STATIC_THROTTLE_FACTOR', 1)

    def genrate_tokens(self, count=10):
        ls = []
        for _ in range(count):
            token = self.token_set.create(device=self)
            ls.append(token.token)
        return ls

    def verify_token(self, token, *args, **kwargs):
        verify_allowed, _ = self.verify_is_allowed()
        if verify_allowed:
            match = self.token_set.filter(token=token).first()
            if match is not None:
                match.delete()
                self.throttle_reset()
            else:
                self.throttle_increment()
        else:
            match = None

        return match is not None


class StaticToken(models.Model):
    """
    A single token belonging to a :class:`StaticDevice`.
    .. attribute:: device
        *ForeignKey*: A foreign key to :class:`StaticDevice`.
    .. attribute:: token
        *CharField*: A random string up to 16 characters.
    """
    device = models.ForeignKey(
        StaticDevice,
        related_name='token_set',
        on_delete=models.CASCADE
    )
    token = models.CharField(
        max_length=16,
        default=static_token,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Static Device Token")
        verbose_name_plural = _("Static Device Tokens")


@receiver(models.signals.post_delete, sender=AuthyOneTouchDevice)
@receiver(models.signals.post_delete, sender=AuthySoftTOTPDevice)
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

@receiver(models.signals.post_save, sender=AuthyOneTouchDevice)
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

@receiver(models.signals.post_delete, sender=AuthyUser)
def pre_delete_authy_user(sender, instance, **kwargs):
    deleted = authy_api.users.delete(instance.authy_id)
    if deleted.ok():
        print(deleted.content)
