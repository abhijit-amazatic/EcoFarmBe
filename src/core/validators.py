"""
Custom validators for the project
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

def full_domain_validator(hostname):
    """
    Validate if a given string is a valid domain with tld
    It should not have protocol & path in it
    """
    hostname_pattern = re.compile(r'(?!-)[A-Z\d-]+(?<!-)$', re.IGNORECASE)
    if not hostname:
        return
    if len(hostname) > 255:
        raise ValidationError(_("The domain name cannot be"
                                " composed of more than 255 characters."))
    if "." not in hostname:
        raise ValidationError(_("Invalid domain."))
    for label in hostname.split("."):
        if len(label) > 63:
            raise ValidationError(
                _("The label '%(label)s' is too"
                  " long (maximum is 63 characters).") % {'label': label})
        if not hostname_pattern.match(label):
            raise ValidationError(_("Unallowed characters in"
                                    " label '%(label)s'.") % {'label': label})
