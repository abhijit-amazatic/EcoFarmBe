import uuid
from os import (urandom,)
from base64 import b32encode
from django.apps import apps
from django.utils.encoding import force_str
from django_otp.models import Device
from django_otp.util import hex_validator, random_hex as org_random_hex
from authy.api import AuthyApiClient

from .conf import settings

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)


def key_validator(*args, **kwargs):
    """Wraps hex_validator generator, to keep makemigrations happy."""
    return hex_validator()(*args, **kwargs)


def random_hex_str(length=20):
    # Could be removed once we depend on django_otp > 0.7.5
    return force_str(org_random_hex(length=length))

def random_hex(length=20):
    return org_random_hex(length=length)

def pk_hex():
    return uuid.uuid4().bytes.hex()

def random_hex_32(length=32):
    return org_random_hex(length=length)

def static_token():
    return b32encode(urandom(5)).decode('utf-8').lower()

def phone_number_mask(phone_num_str):
    mask = phone_num_str
    if len(phone_num_str) > 8:
        if phone_num_str[0] == '+':
            mask = phone_num_str[0:3] + '*' * (len(phone_num_str) - 6) + phone_num_str[-3:]
        else:
            mask = phone_num_str[0:2] + '*' * (len(phone_num_str) - 4) + phone_num_str[-2:]
    return mask

def get_two_factor_devices(user_instance, confirmed_only=True):
    return [
        z
        for y in apps.get_models() if issubclass(y, Device)
        for z in y.objects.filter(user=user_instance) if not confirmed_only or z.confirmed
    ]

def validate_authy_callback_request_signature(request):
    if 'X-Authy-Signature' in request.headers and 'X-Authy-Signature-Nonce' in request.headers:
        # url = request.build_absolute_uri(request.path)
        scheme = request.META.get('HTTP_X_FORWARDED_PROTO', request.scheme)
        url = f'{scheme}://{request.get_host()}{request.path}'
        params = {
            'signature': request.headers['X-Authy-Signature'],
            'nonce':     request.headers['X-Authy-Signature-Nonce'],
            'method':    request.method,
            'url':       url,
            'params':    request.data,
        }
        if authy_api.one_touch.validate_one_touch_signature(**params):
            return True
    return False