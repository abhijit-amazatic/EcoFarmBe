from binascii import (hexlify, unhexlify)
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_otp.models import Device, ThrottlingMixin
from django_otp.oath import (TOTP,)
from integration.apps.twilio import (send_sms, make_call,)

from .conf import settings
from .utils import (
    random_hex,
    key_validator,
    phone_number_mask,
)


class AbstractDevice(Device):
    """
    Abstract Device.
    """
    confirmed = models.BooleanField(default=False, help_text="Is this device ready for use?")


    @property
    def type(self):
        return 'base_device'

    @property
    def is_removable(self):
        return True

    @property
    def is_interactive(self):
        return super().is_interactive()

    @property
    def challenge_methods(self):
        return []

    @property
    def device_id(self):
        return hexlify(self.persistent_id.encode('utf-8')).decode('utf-8')

    @classmethod
    def from_device_id(cls, device_id):
        try:
            persistent_id = (unhexlify(device_id)).decode('utf-8')
        except Exception:
            return None
        else:
            return cls.from_persistent_id(persistent_id)
    def generate_challenge(self, *args, **kwargs):
        return None

    generate_challenge.stub = True

    def verify_token(self, token, *args, **kwargs):
        return False

    class Meta(Device.Meta):
        abstract = True


class AbstractPhoneDevice(ThrottlingMixin, AbstractDevice):
    """
    Phone Device.
    """
    name = models.CharField(
        max_length=64,
        help_text="The human-readable name of this device.",
        blank=True,
        default='',
    )
    key = models.CharField(
        max_length=80,
        validators=[key_validator],
        default=random_hex,
        help_text="A hex-encoded secret key of up to 40 bytes.",
    )
    token_timestamp = models.DateTimeField(
        help_text="The timestamp of the token generation.",
        default=timezone.now,
    )
    event_code = models.CharField(
        _('Event Code String'),
        max_length=255,
        default=''
    )

    class Meta(AbstractDevice.Meta):
        abstract = True


    def __str__(self):
        return "{0}".format(self.phone_number)

    @property
    def type(self):
        return 'phone'

    @property
    def challenge_methods(self):
        return ['sms', 'call']

    @property
    def bin_key(self):
        """
        The secret key as a binary string.
        """
        return unhexlify(self.key.encode())

    def generate_token(self, event_code='', commit=True):
        """
        Generates a token.
        Pass 'commit=False' to avoid calling self.save().
        :param str event_code: event_code is a normal string used to verify that token
                               is being used for the same purpose it was generated.
        :param bool commit: Whether to autosave the generated token.
        """
        self.token_timestamp = timezone.now()
        self.event_code = event_code
        if commit:
            self.save()

        totp = self.get_totp_obj()
        return totp.token()

    def get_totp_obj(self):
        """
        return TOTP object.
        """
        _digits = getattr(settings, 'PHONE_TOTP_DIGITS')
        _steps = getattr(settings, 'PHONE_TOTP_STEPS')

        key = self.bin_key
        totp = TOTP(key, step=_steps, digits=_digits, drift=0,)
        totp.time = self.token_timestamp.timestamp()

        return totp

    def verify_token(self, token, event_code=None, **kwargs):

        verify_allowed, _ = self.verify_is_allowed()
        if not verify_allowed:
            return False

        if self.event_code and self.event_code != event_code:
            return False

        seconds_to_expire = 300
        _now = timezone.now()
        _valid_until = self.token_timestamp + timedelta(seconds=seconds_to_expire)

        try:
            token = int(token)
        except Exception:
            verified = False
        else:
            if _now < _valid_until:
                totp = self.get_totp_obj()
                verified = totp.verify(token, tolerance=0, min_t=None)
                if verified:
                    self.token_timestamp = timezone.now()
                    self.event_code = 'unusable_token_' + random_hex(5)
                    self.throttle_reset(commit=False)
                    self.save()
            else:
                verified = False

        if not verified:
            self.throttle_increment(commit=True)

        return verified

    def get_throttle_factor(self):
        return getattr(settings, 'PHONE_TOTP_THROTTLE_FACTOR', 1)

    def save(self, *args, **kwargs):
        if hasattr(self, 'phone_number'):
            self.name = 'phone ' + phone_number_mask(self.phone_number.as_e164)
        super().save(*args, **kwargs)

    def send_otp(self, msg=None, event_code='',):
        """
        send totp token via sms.
        :param str msg: Message to send on phone with place holder 'XXXX' for otp.
        """
        return self.generate_challenge(msg=msg, event_code=event_code)

    def send_otp_call(self, msg=None, event_code=''):
        """
        send totp token via call.
        :param str msg: Message to send on phone with place holder 'XXXX' for otp.
        """
        return self.generate_challenge(msg=msg, method='call', event_code=event_code)

    def generate_challenge(self, msg=None, method='sms', event_code='', **kwargs):
        """
        send totp token
        :param str msg: Message to send on phone with place holder 'XXXX' for otp.
        """
        token = str(self.generate_token(event_code=event_code))
        if method == 'call':
            token = ' '.join(list(token))

        if msg and 'XXXX' in msg:
            body_text = msg.replace('XXXX', token)
        else:
            body_text = f'Your verification code for Thrive Society is {token}.'
        if hasattr(self, 'phone_number'):
            to = self.phone_number
            if hasattr(to, 'as_e164'):
                to = to.as_e164

            if method == 'call':
                ret = make_call(to=to, body_plain=body_text)
                if not isinstance(ret, Exception)and not getattr(ret, 'error_code', None):
                    return (True, {'detail': 'Verification call request made.'})
                else:
                    return (False, {'detail': 'Unable to make Verification call.'})
            elif method == 'sms':
                ret = send_sms(to=to, body=body_text)
                if not isinstance(ret, Exception) and not getattr(ret, 'error_code', None):
                    return (True, {'detail': 'Verification sms is sent.'})
                else:
                    return (False, {'detail': 'Unable to send Verification sms.'})
            return (False, {'detail': f'method {method} is not supported'})
        else:
            return (False, {'detail': 'device has no phone number.'})
