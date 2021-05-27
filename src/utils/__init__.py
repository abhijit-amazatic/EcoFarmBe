import base64
from django.conf import settings
from django.shortcuts import reverse

def reverse_admin_change_path(obj):
    return reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
        args=(obj.id,),
    )


def get_fernet_key(salt:str=None):
    key = (settings.SECRET_KEY * int(1 + 32//len(settings.SECRET_KEY)))[:32]
    if salt:
        key = salt + key[len(salt):]
    return base64.urlsafe_b64encode((key[:32].encode('utf-8'))).decode('utf-8')

def base64_url_encode(string):
    """
    Removes any `=` used as padding from the encoded string.
    """
    encoded = base64.urlsafe_b64encode(string)
    return encoded.rstrip("=")

def base64_url_dencode(string):
    """
    Adds back in the required padding before decoding.
    """
    padding = 4 - (len(string) % 4)
    string = string + ("=" * padding)
    return base64.urlsafe_b64decode(string)