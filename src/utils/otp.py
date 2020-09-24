from django.utils.encoding import force_str
from django_otp.util import hex_validator, random_hex


def key_validator(*args, **kwargs):
    """Wraps hex_validator generator, to keep makemigrations happy."""
    return hex_validator()(*args, **kwargs)


def random_hex_str(length=20):
    # Could be removed once we depend on django_otp > 0.7.5
    return force_str(random_hex(length=length))