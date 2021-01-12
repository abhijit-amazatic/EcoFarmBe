"""
Brand related schemas defined here.
"""
import time
from datetime import timedelta
from base64 import (urlsafe_b64encode, urlsafe_b64decode)

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission as DjPermission
from django.contrib.postgres.fields import (ArrayField, JSONField, HStoreField,)
from django.contrib.contenttypes.fields import (GenericRelation, )
from django.conf import settings
from django.utils import timezone

from multiselectfield import MultiSelectField
from phonenumber_field.modelfields import PhoneNumberField
from cryptography.fernet import (Fernet, InvalidToken)

from core.mixins.models import (StatusFlagMixin, TimeStampFlagModelMixin, )
from core.validators import full_domain_validator
from user.models import User
from inventory.models import (Documents, )
from .exceptions import (InvalidInviteToken, ExpiredInviteToken,)


FERNET_KEY = (settings.SECRET_KEY * int(1 + 32//len(settings.SECRET_KEY)))[:32]
FERNET_KEY = urlsafe_b64encode((FERNET_KEY.encode('utf-8'))).decode('utf-8')
fernet = Fernet(FERNET_KEY)


class Organization(TimeStampFlagModelMixin,models.Model):
    """
    Stores Organization's details.
    """
    name = models.CharField(_('Organization Name'), max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Created By'),
        related_name='organizations',
        on_delete=models.CASCADE
    )
    zoho_crm_id = models.CharField(_('Zoho CRM ID'), max_length=100, blank=True, null=True)
    is_updated_in_crm = models.BooleanField(_('Is Updated In CRM'), default=False)
    email = models.EmailField(_('Email Address'), null=True, blank=True)
    phone = PhoneNumberField(_('Phone'), null=True, blank=True)
    category = models.CharField(_('Category'), max_length=255, null=True, blank=True)
    about = models.TextField(_('description'), null=True, blank=True)
    ethics_and_certifications = ArrayField(models.CharField(_('Ethics And Certifications'), max_length=255, blank=True), blank=True, null=True, default=list)
    documents = GenericRelation(Documents)

    class Meta:
        unique_together = (('name', 'created_by'), )
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')

    def __str__(self):
        return self.name


class PermissionGroup(models.Model):
    """
    The permission Group.
    """
    name = models.CharField(
        _('Name'),
        max_length=100,
        unique=True,
    )

    class Meta:
        verbose_name = _('Permission Group')
        verbose_name_plural = _('Permission Groups')
        ordering = ('name',)

    def __str__(self):
        return self.name


class Permission(models.Model):
    """
    The permissions.
    """
    id = models.CharField(
        _('Id'),
        max_length=100,
        unique=True,
        primary_key=True,
    )
    name = models.CharField(
        _('Name'),
        max_length=100,
    )

    description = models.TextField(_('description'), null=True, blank=True)
    group = models.ForeignKey(
        PermissionGroup,
        verbose_name=_('Group'),
        related_name='permissions',
        on_delete=models.PROTECT
    )

    # def save(self, *args, **kwargs):
    #     self.group = PERMISSION_GROUP_MAP[self.codename]
    #     return super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        ordering = ('group__name', 'id')

    def __str__(self):
        return f"{self.group} | {self.name}"

    def natural_key(self):
        return (self.name,)


class OrganizationRole(TimeStampFlagModelMixin, models.Model):
    """
    Stores Organization User's Roles.
    """
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('Organization'),
        related_name='roles',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name=_('Name'),
        max_length=60,
    )
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('Permissions'),
        blank=True,
    )

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    class Meta:
        unique_together = (('organization', 'name'), )
        verbose_name = _('Organization Role')
        verbose_name_plural = _('Organization Roles')


class OrganizationUser(TimeStampFlagModelMixin, models.Model):
    """
    Stores Brand's details.
    """
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('Organization'),
        related_name='organization_user',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('User'),
        related_name='organization_user',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (('organization', 'user'), )
        verbose_name = _('Organization User')
        verbose_name_plural = _('Organization Users')

    def __str__(self):
        return f'{self.organization} | {self.user}'


class Brand(TimeStampFlagModelMixin, models.Model):
    """
    Stores Brand's details.
    """
    brand_name = models.CharField(_('Brand Name'),max_length=255,unique=True)
    # parent_brand = models.ForeignKey('self', blank=True, null=True, default=None, on_delete=models.CASCADE)
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('Organization'),
        related_name='brands',
        on_delete=models.CASCADE,
    )
    brand_category = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    product_category = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    brand_county = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    region = models.CharField(_('Region'), blank=True, null=True, max_length=255)
    appellation = models.CharField(_('Brand Appellation'), blank=True, null=True, max_length=255)
    ethics_and_certification = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    about_brand = models.TextField(blank=True, null=True)
    interested_in_co_branding = models.CharField(blank=True, null=True, max_length=255)
    have_marketing = models.CharField(blank=True, null=True, max_length=255)
    featured_on_our_site = models.CharField(blank=True, null=True, max_length=255)
    profile_category = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    is_buyer = models.BooleanField(_('Is Buyer/accounts'), default=False)
    is_seller = models.BooleanField(_('Is Seller/Vendor'), default=False)
    is_updated_in_crm = models.BooleanField(_('Is Updated In CRM'), default=False)
    zoho_crm_id = models.CharField(_('Zoho CRM ID'), max_length=100, blank=True, null=True)
    zoho_books_id = models.CharField(_('Zoho Books ID'), max_length=100, blank=True, null=True)
    brand_image = models.CharField( _('Brand Image'), blank=True, null=True, max_length=255)
    documents = GenericRelation(Documents)

    def __str__(self):
        return self.brand_name


class License(TimeStampFlagModelMixin,StatusFlagMixin, models.Model):
    """
    Stores License Profile for either related to brand or individual user-so category & buyer and seller.
    """
    brand = models.ForeignKey(Brand, verbose_name=_('Brand'), on_delete=models.CASCADE, blank=True, null=True)
    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Created By'), on_delete=models.CASCADE,)
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('Organization'),
        related_name='licenses',
        on_delete=models.CASCADE,
    )
    license_type = models.CharField(
        _('License Type'), blank=True, null=True, max_length=255)
    owner_or_manager = models.CharField(
        _('Owner or Manager'), blank=True, null=True, max_length=12)
    legal_business_name = models.CharField(
        _('Legal Business Name'), blank=True, null=True, max_length=255)
    license_number = models.CharField(
        _('License Number'), blank=True, null=True, max_length=255)
    expiration_date = models.DateField(
        _('Expiration Date'), blank=True, null=True, default=None)
    issue_date = models.DateField(
        _('Issue Date'), blank=True, null=True, default=None)
    premises_address = models.TextField(blank=True, null=True)
    premises_county = models.CharField(
        _('Premises County'), blank=True, null=True, max_length=255)
    business_structure = models.CharField(
        _('Business sructure'), blank=True, null=True, max_length=255)
    tax_identification = models.CharField(
        _('Tax Identification'), blank=True, null=True, max_length=255)
    ein_or_ssn = models.CharField(
        _('EIN or SSN'), blank=True, null=True, max_length=255)
    premises_city = models.CharField(
        _('Premises City'), blank=True, null=True, max_length=255)
    zip_code = models.CharField(
        _('Premises Zip'), blank=True, null=True, max_length=255)
    premises_apn = models.CharField(
        _('Premises APN'), blank=True, null=True, max_length=255)
    premises_state = models.CharField(
        _('Premises State'), blank=True, null=True, max_length=255)
    uploaded_license_to = models.CharField(
        _('Uploaded To'), blank=True, null=True, max_length=255)
    uploaded_sellers_permit_to = models.CharField(
        _('Uploaded Sellers Permit To'), blank=True, null=True, max_length=255)
    uploaded_w9_to = models.CharField(
        _('Uploaded W9  To'), blank=True, null=True, max_length=255)
    associated_program = models.CharField(
        _('Associated_program'), blank=True, null=True, max_length=255)
    profile_category = models.CharField(_('Profile Category'), blank=True, null=True, max_length=255)
    is_buyer = models.BooleanField(_('Is Buyer/accounts(if individual user)'), default=False)
    is_seller = models.BooleanField(_('Is Seller/Vendor(if individual user)'), default=False)
    is_updated_in_crm = models.BooleanField(_('Is Updated In CRM'), default=False)
    zoho_crm_id = models.CharField(_('Zoho CRM ID'), max_length=100, blank=True, null=True)
    zoho_books_id = models.CharField(_('Zoho Books ID'), max_length=100, blank=True, null=True)
    documents = GenericRelation(Documents)
    is_data_fetching_complete = models.BooleanField(_('Is crm data fetched for existing user'), default=False)
    status_before_expiry = models.CharField(_('License status before expiry'), max_length=100, blank=True, null=True)
    is_updated_via_trigger = models.BooleanField(_('Is Updated Via Trigger'), default=False)

    def __str__(self):
        return self.legal_business_name

    class Meta:
        verbose_name = _('License/Profile')


class OrganizationUserRole(TimeStampFlagModelMixin, models.Model):
    """
    Stores Brand's details.
    """
    organization_user = models.ForeignKey(
        OrganizationUser,
        verbose_name=_('Organization User'),
        related_name='organization_user_role',
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        OrganizationRole,
        verbose_name=_('Organization Role'),
        related_name='organization_user_role',
        on_delete=models.CASCADE,
    )
    licenses = models.ManyToManyField(
        License,
        verbose_name=_('Licenses'),
    )

    class Meta:
        unique_together = (('organization_user', 'role'), )
        verbose_name = _('Organization User Role')
        verbose_name_plural = _('Organization User Roles')

    def __str__(self):
        return f'{self.organization_user} | {self.role}'

def get_invite_expiration_time():
    return timezone.now() + timedelta(hours=48)

class OrganizationUserInvite(TimeStampFlagModelMixin, models.Model):
    """
    Stores Brand's details.
    """
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('completed', _('Completed')),
    )
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('Organization'),
        related_name='invites',
        on_delete=models.CASCADE,
    )
    full_name = models.CharField(_('Full Name'), max_length=200)
    email = models.EmailField(_('Email Address'), )
    phone = PhoneNumberField(_('Phone'), )
    role = models.ForeignKey(
        OrganizationRole,
        verbose_name=_('Organization Role'),
        related_name='invites',
        on_delete=models.CASCADE,
    )
    licenses = models.ManyToManyField(
        License,
        verbose_name=_('Licenses'),
        blank=True,
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

    class Meta:
        verbose_name = _('Organization User Invite')
        verbose_name_plural = _('Organization User Invites')

    def __str__(self):
        return f'{self.email} | {self.role}'

    def get_invite_token(self):
        context = "{0}|{1}|{2}".format(self.id, self.email, 'inviteToken')
        return urlsafe_b64encode(fernet.encrypt(context.encode('utf-8'))).decode('utf-8')

    @classmethod
    def get_object_from_invite_token(cls, token):
        TTL = timedelta(hours=48).total_seconds()
        # TTL = 10
        _MAX_CLOCK_SKEW = 60
        current_time = int(time.time())
        try:
            token_data = urlsafe_b64decode(token.encode('utf-8'))
            timestamp = fernet.extract_timestamp(token_data)
            if timestamp + TTL < current_time:
                raise ExpiredInviteToken
            if current_time + _MAX_CLOCK_SKEW < timestamp:
                raise InvalidInviteToken
            context = fernet.decrypt(token_data).decode('utf-8')
            obj_id, email, event_code = context.split('|')
            if not event_code == 'inviteToken':
                raise InvalidInviteToken
            obj = cls.objects.get(id=int(obj_id), email=email)
        except InvalidToken:
            raise InvalidInviteToken
        except (InvalidInviteToken, ExpiredInviteToken) as e:
            raise e
        except Exception as e:
            print(e.with_traceback)
            raise InvalidInviteToken
        else:
            return obj



# class LicenseRole(TimeStampFlagModelMixin, models.Model):
#     """
#     Stores License Profile User's User's Roles.
#     """
#     ROLE_OWNER = 'owner'
#     ROLE_LICENSE_OWNER = 'license_owner'
#     ROLE_FARM_MANAGER = 'farm_manager'
#     ROLE_LOGISTICS = 'logistics'
#     ROLE_SALES_OR_INVENTORY = 'sales_or_inventory'
#     ROLE_BILLING = 'billing'
#     ROLE_CHOICES = (
#         (ROLE_OWNER, _('Owner')),
#         (ROLE_LICENSE_OWNER, _('License Owner')),
#         (ROLE_FARM_MANAGER, _('Farm Manager')),
#         (ROLE_LOGISTICS, _('Logistics')),
#         (ROLE_SALES_OR_INVENTORY, _('Sales or Inventory')),
#         (ROLE_BILLING, _('Billing')),
#     )
#     ROLE_CHOICES_DICT = dict(ROLE_CHOICES)
#     name = models.CharField(
#         verbose_name=_('Name'),
#         max_length=60,
#         choices=ROLE_CHOICES,
#         unique=True,
#     )
#     default_permissions = models.ManyToManyField(
#         DjPermission,
#         verbose_name=_('Default Permissions'),
#         blank=True,
#         limit_choices_to=Q(content_type__app_label='brand'),
#     )


#     def __str__(self):
#         return str(self.ROLE_CHOICES_DICT.get(self.name, ''))

#     def natural_key(self):
#         return (self.name,)

#     class Meta:
#         verbose_name = _('License Role')
#         verbose_name_plural = _('License Roles')


# class LicenseUser(TimeStampFlagModelMixin,models.Model):
#     """
#     Stores License Profile User's details #combined roles for all accounts & vendors.
#     Only farm manager is extra in vendors/sellers.
#     """
#     license = models.ForeignKey(License, verbose_name=_('License'),
#                              related_name='profile_roles', on_delete=models.CASCADE)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'),
#                              related_name='license_roles', on_delete=models.CASCADE)
#     role = models.ManyToManyField(LicenseRole, verbose_name=_('Role'), related_name='license_users')

#     def __str__(self):
#         return f'{self.license} | {self.user}'

#     class Meta:
#         unique_together = (('license', 'user'), )
#         verbose_name = _('License Profile User')
#         verbose_name_plural = _('License Profile Users')


# class LicenseRolePermissions(TimeStampFlagModelMixin,models.Model):
#     """
#     Stores License Profile Role's Permissions.
#     """
#     license = models.ForeignKey(License, verbose_name=_('License'),
#                              related_name='license_role_permissions', on_delete=models.CASCADE)
#     role = models.ForeignKey(LicenseRole, verbose_name=_('Role'),
#                              related_name='license_role_permissions', on_delete=models.CASCADE)
#     permissions = models.ManyToManyField(
#         DjPermission,
#         verbose_name=_('License Role Permissions'),
#         blank=True,
#         limit_choices_to=Q(content_type__app_label='brand'),
#     )

#     def __str__(self):
#         return self.name

#     class Meta:
#         unique_together = (('license', 'role'), )
#         verbose_name = _('License Role Permissions')
#         verbose_name_plural = _('License Roles Permissions')



class ProfileContact(models.Model):
    """
    Stores people, company, billing and mailing address.
    """
    license = models.OneToOneField(License, verbose_name=_('LicenseProfile'),
                                related_name='profile_contact', on_delete=models.CASCADE)
    profile_contact_details = JSONField(null=False, blank=False, default=dict)
    is_draft = models.BooleanField(_('Is Draft'), default=False)


class LicenseProfile(TimeStampFlagModelMixin,models.Model):
    """
    It is farm profile/Account profile in UI.Stores Farm data.Vendors are essentially replica of license.
    """
    license = models.OneToOneField(License, verbose_name=_('LicenseProfile'),
                                related_name='license_profile', on_delete=models.CASCADE)
    brand_association = models.ForeignKey(Brand, verbose_name=_('Brand'), on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(_('Name'), blank=True, null=True, max_length=255)
    county = models.CharField(
        _('County'), blank=True, null=True, max_length=255)
    appellation = models.CharField(_('Appellation'), blank=True, null=True, max_length=255)
    region = models.CharField(_('Region'), blank=True, null=True, max_length=255)
    ethics_and_certification = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    product_of_interest = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    cultivars_of_interest = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    about = models.TextField(blank=True, null=True)
    other_distributors = models.CharField(blank=True, null=True, max_length=255)
    transportation = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    issues_with_failed_labtest = models.CharField(blank=True, null=True, max_length=255)
    preferred_payment = models.CharField(_('Preferred Payment'), blank=True, null=True, max_length=255)
    approved_on = models.DateTimeField(_('Approved on'), blank=True, null=True)
    approved_by = JSONField(_('Approved by'), null=True, blank=True, default=dict)
    agreement_signed = models.BooleanField(_('Is Agreement Signed'), default=False)
    agreement_link = models.CharField(_('Box Agreement Link'), max_length=100, blank=True, null=True)
    is_draft = models.BooleanField(_('Is Draft'), default=False)
    farm_profile_photo = models.CharField(
        _('Farm Profile Photo Box ID'), blank=True, null=True, max_length=255)
    farm_photo_sharable_link = models.CharField(
        _('Farm Profile Photo Sharable Link'), blank=True, null=True, max_length=255)
    is_updated_in_crm = models.BooleanField(_('Is Updated In CRM'), default=False)
    zoho_crm_id = models.CharField(_('Zoho CRM ID'), max_length=100, blank=True, null=True)
    lab_test_issues = models.TextField(blank=True, null=True)


class CultivationOverview(models.Model):
    """
    This is profile_overview in old DB schema.
    """
    license = models.OneToOneField(License, verbose_name=_('License'),
                                   related_name='cultivation_overview', on_delete=models.CASCADE)
    autoflower = models.BooleanField(_('Is Agreement Signed'), default=False)
    full_season = models.BooleanField(_('Is Agreement Signed'), default=False)
    lighting_type = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    type_of_nutrients = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    overview = ArrayField(HStoreField(blank=True, null=True), blank=True, null=True,default=list)
    is_draft = models.BooleanField(_('Is Draft'), default=False)

class ProgramOverview(models.Model):
    """
    Stores program overview.
    """
    license = models.OneToOneField(License, verbose_name=_('License'),
                                related_name='program_overview', on_delete=models.CASCADE)
    program_details = JSONField(null=False, blank=False, default=dict)
    is_draft = models.BooleanField(_('Is Draft'), default=False)

class FinancialOverview(models.Model):
    """
    Stores farm's Financial overview.
    """
    license = models.OneToOneField(License, verbose_name=_('License'),
                                related_name='financial_overview', on_delete=models.CASCADE)
    know_annual_budget = models.CharField(blank=True, null=True, max_length=255)
    annual_budget = models.CharField(_('Annual Budget'), blank=True, null=True, max_length=255)
    overview = ArrayField(HStoreField(blank=True, null=True), blank=True, null=True, default=list)
    is_draft = models.BooleanField(_('Is Draft'), default=False)

class CropOverview(models.Model):
    """
    Stores farm's  farm's Processing overview i.e. crop overview.
    """
    license = models.OneToOneField(License, verbose_name=_('License'),
                                related_name='crop_overview', on_delete=models.CASCADE)
    process_on_site = models.CharField(blank=True, null=True, max_length=255)
    need_processing_support = models.CharField(blank=True, null=True, max_length=255)
    overview = ArrayField(JSONField(blank=True,null=True), blank=True, null=True, default=list)
    is_draft = models.BooleanField(_('Is Draft'), default=False)


class BillingInformation(models.Model):
    """
    Stores farm's  farm's Processing overview i.e. crop overview.
    """
    license = models.OneToOneField(License, verbose_name=_('License'),
                                related_name='billing_information', on_delete=models.CASCADE)
    preferred_payment = ArrayField(models.CharField(max_length=255, blank=True), blank=True, null=True, default=list)
    bank_routing_number = models.CharField(_('Bank Routing Number'), blank=True, null=True, max_length=255)
    bank_account_number = models.CharField(_('Bank Account Number'), blank=True, null=True, max_length=255)
    bank_name = models.CharField(_('Bank Name'), null=True, blank=True, max_length=255)
    bank_street = models.CharField(_('Bank Street'), null=True, blank=True, max_length=255)
    bank_city  = models.CharField(_('Bank City'), null=True, blank=True, max_length=255)
    bank_zip_code  = models.CharField(_('Bank Zip Code '), null=True, blank=True, max_length=255)


class ProfileCategory(models.Model):
    """
    Class implementing  Vendor/Profile categories.
    """
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Vendor/Profile Category')
        verbose_name_plural = _('Vendor/Profile Categories')

class ProfileReport(models.Model):
    """
    Stores reports/calculation data.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Report Manager'),on_delete=models.CASCADE)
    profile = models.CharField( _('Vendor Profile'), blank=True, null=True, max_length=255)
    report_name = models.CharField( _('Report Name'), blank=True, null=True, max_length=255)
    profile_type = ArrayField(models.CharField(max_length=255, blank=True), blank=True, null=True, default=list)
    profile_reports = JSONField(null=False, blank=False, default=dict)
