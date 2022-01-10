"""
Model for integrations.
"""
from django.db import models
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from django.utils.translation import ugettext_lazy as _
from core.mixins.models import (StatusFlagMixin, TimeStampFlagModelMixin)

class Integration(models.Model):
    name = models.CharField(_('Name'), max_length=255, unique=True)
    client_id = models.CharField(_('Client ID'), max_length=255, blank=True, null=True)
    client_secret = models.CharField(_('Client Secret'), max_length=255, blank=True, null=True)
    access_token = models.CharField(_('Access Token'), max_length=255)
    refresh_token = models.CharField(_('Refresh Token'), max_length=255)
    access_expiry = models.DateTimeField(_('Access Expiry'), blank=True, null=True)
    refresh_expiry = models.DateTimeField(_('Refresh Expiry'), blank=True, null=True)
    expiry_time = models.BigIntegerField(_('expiry_time_crm'), blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('integration')
        verbose_name_plural = _('integrations')


        
class ConfiaCallback(TimeStampFlagModelMixin, models.Model):
    """
    Model to save confia callback data after onboarding.
    """
    partner_company_id = models.CharField(_('client ID'), max_length=255, blank=True, null=True)
    confia_member_id = models.CharField(_('confia Member ID'), max_length=255, blank=True, null=True)
    status = models.CharField(_('status'), max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.partner_company_id if self.partner_company_id else ""

    class Meta:
        verbose_name = _('Confia Onboarding')



class BoxSignDocType(TimeStampFlagModelMixin, models.Model):
    """
    Store sign Document Type.
    """
    DOC_TYPE_CHOICES = (
        ('agreement', _('Agreement')),
        ('w9', _('W9')),
    )
    name = models.CharField(_('Name'), choices=DOC_TYPE_CHOICES, unique=True, primary_key=True, max_length=100)
    display_name = models.CharField(_('Display Name'), max_length=100)
    need_approval = models.BooleanField(_('Need Approval'), default=False)

    class Meta:
        verbose_name = _('Box Sign Doc Type')
        verbose_name_plural = _('Box Sign Doc Type')

    def __str__(self):
        return self.display_name

class BoxSignDocApprover(TimeStampFlagModelMixin, models.Model):
    """
    Store sign Document Approver.
    """
    doc_type = models.OneToOneField(
        BoxSignDocType,
        verbose_name=_("Doc Type"),
        related_name='approver',
        on_delete=models.CASCADE,
    )

    name = models.CharField(_('Approver Name'), max_length=255)
    email = models.EmailField(_('Approver Email'), max_length=255)
    prefill_data = JSONField(_('Approver prefill Data'), blank=True, default=dict)

    class Meta:
        verbose_name = _('Box Sign Doc Approver')
        verbose_name_plural = _('Box Sign Doc Approvers')

    def get_prefill_data(self):
        prefill_data = self.prefill_data or {}
        prefill_data.setdefault('approver_name', self.name)
        prefill_data.setdefault('approver_email', self.email)
        return prefill_data



class BoxSignFinalCopyReader(TimeStampFlagModelMixin, models.Model):
    """
    Store sign Document Approver.
    """
    doc_type = models.ForeignKey(
        BoxSignDocType,
        verbose_name=_("Doc Type"),
        related_name='final_copy_readers',
        on_delete=models.CASCADE,
    )
    name = models.CharField(_('Name'), max_length=255)
    email = models.EmailField(_('Email'), max_length=255)

    class Meta:
        verbose_name = _('Box Sign Final Copy Reader')
        verbose_name_plural = _('Box Sign Final Copy Readers')



# class BoxSignDocTypePrefillField(TimeStampFlagModelMixin,models.Model):
#     """
#     Store sign Document Type.
#     """
#     FIELD_TYPE_CHOICES = (
#         ('text', _('Text')),
#         ('date', _('Date')),
#         ('boolen', _('Boolen')),
#     )
#     doc_type = models.ForeignKey(
#         BoxSignDocType,
#         verbose_name=_('License'),
#         related_name='box_sign_requests',
#         on_delete=models.CASCADE,
#     )
#     id = models.CharField(_('Field ID'), max_length=255, unique=True, primary_key=True)
#     field_type = models.CharField(_('field Type'), choices=FIELD_TYPE_CHOICES, max_length=50)

#     class Meta:
#         verbose_name = _('Box Sign Doc Type Prefill Field')
#         verbose_name_plural = _('Box Sign Doc Type Prefill Fields')


class BoxSign(TimeStampFlagModelMixin,models.Model):
    """
    Store sign request ids.
    """
    license = models.ForeignKey(
        'brand.License',
        verbose_name=_('License'),
        related_name='box_sign_requests',
        on_delete=models.CASCADE,
    )

    doc_type = models.ForeignKey(
        BoxSignDocType,
        verbose_name=_('License'),
        related_name='box_sign_requests',
        on_delete=models.CASCADE,
    )
    request_id = models.CharField(_('Request ID'), unique=True, max_length=255)

    status = models.CharField(_('Status'), blank=True, null=True, max_length=255)
    output_file_id = models.CharField(_('Action ID'), unique=True, max_length=255)
    signer_decision = models.CharField(_('Signer Decision'), blank=True, null=True, max_length=255)
    signer_embed_url = models.URLField(_('Signer Embed URL'), blank=True, null=True, max_length=255)
    program_name = models.CharField(_('Program Name'), blank=True, null=True, max_length=255)
    fields = JSONField(null=True, blank=True, default=dict)
    response = JSONField(null=True, blank=True, default=dict)

    class Meta:
        verbose_name = _('Box Sign Request')
        verbose_name_plural = _('Box Sign Requests')


class BoxEventTracker(TimeStampFlagModelMixin,models.Model):
    """
    Store Box Event Tracker data.
    """
    id = models.CharField(_('Tracker ID'), unique=True, primary_key=True, max_length=255)
    stream_position = models.BigIntegerField(_('Stream Position'), default=0)
    is_state_ideal = models.BooleanField(_("Is State Ideal"), default=True)

    class Meta:
        verbose_name = _('Box Event Tracker')
        verbose_name_plural = _('Box Event Trackers')
