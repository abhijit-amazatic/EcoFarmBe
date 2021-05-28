from base64 import (urlsafe_b64encode, urlsafe_b64decode)

import time
import traceback
from datetime import timedelta
from base64 import (urlsafe_b64encode, urlsafe_b64decode)

from django.db import models
from django.db.models import Q
from django.db.models.deletion import SET_NULL
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils import timezone

from cryptography.fernet import (Fernet, InvalidToken)

from core.mixins.models import (StatusFlagMixin, TimeStampFlagModelMixin, )
from utils import get_fernet_key
from user.models import User
from brand.models import (Organization, OrganizationRole, License)
from .exceptions import (InvalidInviteToken, ExpiredInviteToken,)



# Create your models here.


class InternalOnboardingInvite(TimeStampFlagModelMixin, models.Model):
    """
    Stores Brand's details.
    """
    fernet = Fernet(get_fernet_key(salt='intinv'))
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('user_joining_platform', _('User Joining Platform')),
        ('completed', _('Completed')),
    )
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('Organization'),
        related_name='invites',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        verbose_name=_('Organization'),
        related_name='internal_onboarding_invite',
        on_delete=models.CASCADE,
    )
    license = models.ForeignKey(
        License,
        verbose_name=_('Licenses'),
        related_name='invites',
        on_delete=models.CASCADE,
    )
    roles = models.ManyToManyField(
        OrganizationRole,
        verbose_name=_('Organization Roles'),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Created By'),
        related_name='invited_users',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=60,
        choices=STATUS_CHOICES,
        default='pending',
    )
    completed_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Internal Onboarding Invite')
        verbose_name_plural = _('Internal Onboarding Invites')

    def __str__(self):
        return f'{self.user} | {self.license}'

    def get_invite_token(self):
        context = "{0}|{1}|{2}".format(self.id, self.user_id,)
        token_bytes = self.fernet.encrypt(context.encode('utf-8'))
        # removing '=' to use token as url param
        return token_bytes.decode('utf-8').rstrip("=")

    @classmethod
    def get_object_from_invite_token(cls, token):
        TTL = timedelta(days=7).total_seconds()
        _MAX_CLOCK_SKEW = 60
        current_time = int(time.time())
        try:
            token_data = token + ('=' * (4 - len(token) % 4))
            token_data = token_data.encode('utf-8')
            timestamp = cls.fernet.extract_timestamp(token_data)
            if timestamp + TTL < current_time:
                raise ExpiredInviteToken
            if current_time + _MAX_CLOCK_SKEW < timestamp:
                raise InvalidInviteToken
            context = cls.fernet.decrypt(token_data).decode('utf-8')
            obj_id, user_id, license_id = context.split('|')
            obj = cls.objects.get(id=int(obj_id), user_id=user_id, license_id=license_id)
        except (InvalidToken, cls.DoesNotExist):
            raise InvalidInviteToken
        except (InvalidInviteToken, ExpiredInviteToken) as e:
            raise e
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            raise InvalidInviteToken
        else:
            return obj