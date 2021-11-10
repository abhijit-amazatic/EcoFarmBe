"""
Serializer to validate brand related modules.
"""

import requests
from tempfile import TemporaryFile

from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import (empty, )
from phonenumber_field.serializerfields import PhoneNumberField

from core.settings import (AWS_BUCKET, )
from user.models import User
from inventory.models import (Documents, )
from core.utility import (email_admins_on_profile_registration_completed,notify_admins_on_slack_complete,)
from inventory.models import (Documents, )
from integration.crm import (insert_records,is_user_existing,)
from integration.box import upload_file
from integration.books import(create_customer_in_books, )
from integration.apps.aws import (create_presigned_url, )
from integration.tasks import (
    update_in_crm_task,
    update_license_task,
    insert_record_to_crm,
    update_account_cultivars_of_interest_in_crm,
)
from user.models import (User,)
from cultivar.models import (Cultivar,)
from .tasks import (onboarding_fetched_data_insert_to_db,)
from .serializers_mixin import (
    NestedModelSerializer,
    OrganizationUserRoleRelatedField,
    OrganizationUserRoleRelatedRoleField,
    OrganizationUserRoleRelatedLicenseField,
    InviteUserRelatedField,
    InviteUserTokenField,
    LicenseProfileBrandAssociationField,
)
from .models import (
    Organization,
    Brand,
    License,
    ProfileContact,
    LicenseProfile,
    CultivationOverview,
    NurseryOverview,
    ProgramOverview,
    FinancialOverview,
    CropOverview,
    # BillingInformation,
    ProfileReport,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
    # Permission,
    OnboardingDataFetch,
    LicenseUserInvite,
)

from utils import (reverse_admin_change_path,)


def insert_or_update_vendor_accounts(profile, instance):
    """
    Insert/update vendors/accounts based on existing user or not. 
    is_user_existing returns tuple e.g (False, None)
    """
    is_existing_user = is_user_existing(license_number=instance.license_number)
    if is_existing_user and is_existing_user[0]:
        is_update = True
    else:
        is_update = False

    insert_record_to_crm.delay(license_id=instance.id, is_update=is_update)

    # if is_existing_user and is_existing_user[0]:
    #     if profile.license.profile_category == 'cultivation':
    #         insert_vendors.delay(id=instance.id, is_update=True)
    #     else:
    #         insert_accounts.delay(id=instance.id,is_update=True)
    # else:
    #     if profile.license.profile_category == 'cultivation':
    #         insert_vendors.delay(id=instance.id)
    #     else:
    #         insert_accounts.delay(id=instance.id)

class OrganizationSerializer(serializers.ModelSerializer):
    """
    This defines ProgramOverviewSerializer
    """
    class Meta:
        model = Organization
        exclude = ('created_by',)
        read_only_fields = ('created_on', 'updated_on')

    def validate_name(self, value):
        view = self.context['view']
        qs = view.get_queryset()
        if view.action=='create' and qs.filter(name=value).exists():
            raise serializers.ValidationError("Organization name already exist.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update
        """
        updated_instance = super().update(instance, validated_data)
        update_in_crm_task.delay('Orgs', instance.id)
        return updated_instance


class BrandSerializer(NestedModelSerializer, serializers.ModelSerializer):
    """
    This defines Brand serializer.
    """
    document_url = serializers.SerializerMethodField()
    brand_image = serializers.SerializerMethodField()

    def get_document_url(self, obj):
        """
        Return s3 document url.
        """
        try:
            document = Documents.objects.filter(object_id=obj.id, doc_type='profile_image').latest('created_on')
            if document.box_url:
                return document.box_url
            else:
                path = document.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def get_brand_image(self,obj):
        """
        Return brand image link
        """
        return self.get_document_url(obj)

    def validate(self, data):
        if self.partial:
            pass
        return data

    def update(self, instance, validated_data):
        """
        Update
        """
        updated_instance = super().update(instance, validated_data)
        update_in_crm_task.delay('Brands', instance.id)
        return updated_instance

    class Meta:
        model = Brand
        exclude = ('organization',)


class LicenseSerializer(NestedModelSerializer, serializers.ModelSerializer):
    """
    This defines license serializer.
    """
    license_url = serializers.SerializerMethodField()
    seller_permit_url = serializers.SerializerMethodField()
    license_profile_url = serializers.SerializerMethodField()
    is_existing_user = serializers.SerializerMethodField()
    approved_on = serializers.SerializerMethodField()
    data_fetch_token = serializers.CharField(write_only=True, allow_null=True)

    def get_approved_on(self, obj):
        """
        return license profile approve datetime.
        """
        try:
            approved_on = obj.license_profile.approved_on
        except License.license_profile.RelatedObjectDoesNotExist:
            return None
        else:
            return approved_on

    def get_is_existing_user(self, obj):
        """
        return if user is existing user.
        """
        return obj.organization.created_by.existing_member
    
    def get_license_profile_url(self, obj):
        """
        Return s3 license url.
        """
        try:
            document = Documents.objects.filter(object_id=obj.id, doc_type='profile_image').latest('created_on')
            if document.box_url:
                return document.box_url
            else:
                path = document.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None
    
    def get_license_url(self, obj):
        """
        Return s3 license url.
        """
        try:
            license = Documents.objects.filter(object_id=obj.id, doc_type='license').latest('created_on')
            if license.box_url:
                return license.box_url
            else:
                path = license.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def get_seller_permit_url(self, obj):
        """
        Return s3 license url.
        """
        try:
            seller = Documents.objects.filter(object_id=obj.id, doc_type='seller_permit').latest('created_on')
            if seller.box_url:
                return seller.box_url
            else:
                path = seller.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def validate(self, attrs):
        if self.context['view'].action == 'create':
            data_fetch_token = attrs.get('data_fetch_token')
            if not data_fetch_token:
                raise serializers.ValidationError({'data_fetch_token': 'Token is required.'})
            fetch_instance = OnboardingDataFetch.objects.filter(data_fetch_token=data_fetch_token).first()
            if not fetch_instance:
                raise serializers.ValidationError({'data_fetch_token': 'Invalid Token.'})
            else:
                if not fetch_instance.license_number == attrs.get('license_number'):
                    raise serializers.ValidationError({'data_fetch_token': 'Token is not generated for current license number.'})
                if not fetch_instance.owner_verification_status in ('verified', 'licence_data_not_found',):
                    raise serializers.ValidationError({'data_fetch_token': 'Token status not fulfilled'})

        return super().validate(attrs)

    def update(self, instance, validated_data):
        if validated_data.get('status') == 'completed':
            try:
                profile = LicenseProfile.objects.get(license=instance.id)
                admin_link = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(instance)}"
                #email &slack admins
                email_admins_on_profile_registration_completed(instance.created_by.email,profile.name,instance,admin_link)
                notify_admins_on_slack_complete(instance.created_by.email,instance,admin_link)
                #Create zoho books customer
                # if settings.PRODUCTION:
                #     books_ls = ('books_efd', 'books_efl', 'books_efn')
                # else:
                #     books_ls = ('books_efd',)
                #insert or update vendors/accounts
                insert_or_update_vendor_accounts(profile, instance)
                # create_customer_in_books(id=instance.id)
                instance.refresh_from_db()
            except Exception as e:
                print(e)
        user = super().update(instance, validated_data)
        try:
            update_license_task.delay(dba=instance.legal_business_name, license_id=instance.id)
        except License.DoesNotExist:
            print('License Profile does not exist.')
            pass
        return user

    def create(self, validated_data):
        data_fetch_token = validated_data.pop('data_fetch_token')
        validated_data['created_by'] = self.context['request'].user
        fetch_instance = OnboardingDataFetch.objects.filter(data_fetch_token=data_fetch_token).first()
        instance = super().create(validated_data)
        if fetch_instance.owner_verification_status == 'verified':
            onboarding_fetched_data_insert_to_db.delay(self.context['request'].user.id, fetch_instance.id, instance.id)
        return instance

    class Meta:
        model = License
        # fields = ('__all__')
        read_only_fields = (
            'approved_on',
            'approved_by',
            'uploaded_sellers_permit_to',
            'uploaded_license_to',
            'uploaded_w9_to',
            'client_id',
            'zoho_crm_id',
            'zoho_books_customer_ids',
            'zoho_books_vendor_ids',
        )
        exclude = (
            'organization',
            'crm_output',
            'books_output'
        )


class ProfileContactSerializer(serializers.ModelSerializer):
    """
    This defines ProfileContactSerializer
    """
    class Meta:
        model = ProfileContact
        fields = ('__all__')


class CultivationOverviewSerializer(serializers.ModelSerializer):
    """
    This defines CultivationOverviewSerializer
    """
    class Meta:
        model = CultivationOverview
        fields = ('__all__')

class NurseryOverviewSerializer(serializers.ModelSerializer):
    """
    This defines NurseryOverviewSerializer
    """
    def __init__(self, instance=None, data=empty, **kwargs):
        if data is not empty:
            if data.get('pending_cultivars'):
                pending_cultivars = []
                for cultivar in data.get('pending_cultivars', []):
                    if isinstance(cultivar, str):
                        cultivar_obj = Cultivar.objects.create(cultivar_name=cultivar)
                        pending_cultivars.append(cultivar_obj.id)
                    else:
                        pending_cultivars.append(cultivar)
                data['pending_cultivars'] = pending_cultivars
        super().__init__(instance=instance, data=data, **kwargs)

    class Meta:
        model = NurseryOverview
        fields = ('__all__')


class LicenseProfileSerializer(serializers.ModelSerializer):
    """
    This defines LicenseProfileSerializer
    """
    brand_association = LicenseProfileBrandAssociationField(allow_null=True)

    def create(self, validated_data):
        """
        Update for licenseprofile
        """
        instance = super().create(validated_data)
        instance.license.brand = instance.brand_association
        instance.license.save()
        return instance

    def update(self, instance, validated_data):
        """
        Update for licenseprofile
        """
        update_cultivar_of_interest = 'cultivars_of_interest' in validated_data and validated_data.get('cultivars_of_interest') != instance.cultivars_of_interest

        instance = super().update(instance, validated_data)
        if instance.agreement_signed and not instance.signed_program_name:
            if instance.license.profile_category and instance.license.profile_category not in ('cultivation', 'nursery'):
                instance.signed_program_name = 'Silver - Member'
                instance.save()
        instance.license.brand = instance.brand_association
        instance.license.save()
        update_in_crm_task.delay('Accounts', instance.id)
        update_in_crm_task.delay('Vendors', instance.id)
        if update_cultivar_of_interest:
            update_account_cultivars_of_interest_in_crm.delay(instance.id)
        return instance

    class Meta:
        model = LicenseProfile
        read_only_fields = (
            'name',
            'signed_program_name',
            'agreement_link',
            'zoho_crm_account_id',
            'zoho_crm_vendor_id',
            'crm_account_owner_id',
            'crm_vendor_owner_id',
        )

        exclude = (
        )

class FinancialOverviewSerializer(serializers.ModelSerializer):
    """
    This defines FinancialOverviewSerializer
    """
    class Meta:
        model = FinancialOverview
        fields = ('__all__')


class CropOverviewSerializer(serializers.ModelSerializer):
    """
    This defines CropOverviewSerializer
    """
    class Meta:
        model = CropOverview
        fields = ('__all__')


class ProgramOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProgramOverviewSerializer
    """
    class Meta:
        model = ProgramOverview
        fields = ('__all__')

class BillingInformationSerializer(serializers.ModelSerializer):
    """
    This defines BillingInformationSerializer
    """
    class Meta:
        model = LicenseProfile
        fields = (
            'preferred_payment',
            'bank_routing_number',
            'bank_account_number',
            'bank_name',
            'bank_street',
            'bank_city',
            'bank_zip_code',
            'bank_state',
            'bank_country',
        )

    def update(self, instance, validated_data):
        """
        Update for licenseprofile
        """
        updated_instance = super().update(instance, validated_data)
        update_in_crm_task.delay('Accounts', instance.id)
        update_in_crm_task.delay('Vendors', instance.id)
        return updated_instance


class ProfileReportSerializer(serializers.ModelSerializer):
    """
    This defines ProfileReport serializer
    """

    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to upload reports related to his VendorProfile.
        """
        if self.context['request'].method == 'POST':
            if not (obj['user'] == self.context['request'].user):
                raise serializers.ValidationError(
                    "You are not allowed to create report with another user!")

        return obj

    class Meta:
        model = ProfileReport
        fields = ('__all__')


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)
    name = serializers.CharField(read_only=True)
    license = serializers.CharField(write_only=True)

    def create(self, validated_data):
        key = 'uploaded_sellers_permit_to' if 'seller-permit' in validated_data[
            'file'].name else 'uploaded_license_to'
        upload_file('111282192684', validated_data['file'].temporary_file_path(),
                    validated_data['file'].name, validated_data['license'], key)
        return {'name': validated_data['file'].name}


class CurrentPasswordSerializer(serializers.Serializer): # pylint: disable=W0223
    """
    Serializer class to Check current password
    """
    current_password = serializers.CharField(
        label="Current Password",
        required=True,
        max_length=128,
        style={'input_type': 'password'},
        write_only=True,
    )

    def validate_current_password(self, value):
        """
        Check current password.
        """
        user = self.context['request'].user
        if user.is_authenticated:
            if user.check_password(value):
                return value
        raise serializers.ValidationError("wrong current password.")


class OrganizationUserInfoSerializer(serializers.ModelSerializer):
    """
    This defines ProgramOverviewSerializer
    """

    class Meta:
        model = User
        fields = ('id','first_name', 'last_name', 'full_name', 'email', 'phone')


class OrganizationRoleSerializer(NestedModelSerializer, serializers.ModelSerializer):
    """
    This defines organization role serializer.
    """

    class Meta:
        model = OrganizationRole
        exclude = ('organization',)

class OrganizationUserRoleSerializer(serializers.ModelSerializer):
    """
    This defines organization role serializer.
    """
    # organization_user = OrganizationUserRoleRelatedField(
    #     queryset=OrganizationUser.objects.all(),
    # )
    role = OrganizationUserRoleRelatedRoleField(
        queryset=OrganizationRole.objects.all(),
    )
    # role_info = OrganizationRoleSerializer(source='role', read_only=True)
    licenses = OrganizationUserRoleRelatedLicenseField(
        queryset=License.objects.all(),
        many=True,
        # required=True,
    )

    def validate_licenses(self, value):
        """
        Check that license is selected.
        """
        if not value:
            raise serializers.ValidationError("At leat one License must be selected.")
        return value

    class Meta:
        model = OrganizationUserRole
        fields = (
            'id',
            # 'organization_user',
            # 'organization_user_info',
            'role',
            # 'role_info',
            'licenses',
            'created_on',
            'updated_on',
            # 'organization',
        )



class OrganizationUserNestedViewSerializer(NestedModelSerializer, serializers.ModelSerializer):
    """
    This defines organization role serializer.
    """
    user_info = OrganizationUserInfoSerializer(source='user', read_only=True)
    roles_licenses = OrganizationUserRoleSerializer(source='organization_user_role', many=True, read_only=True)
    document_url = serializers.SerializerMethodField()

    def get_document_url(self, obj):
        """
        Return s3 document url.
        """
        try:
            document = Documents.objects.filter(object_id=obj.user.id, doc_type='profile_image').latest('created_on')
            if document.box_url:
                return document.box_url
            else:
                path = document.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    class Meta:
        model = OrganizationUser
        fields = (
            'id',
            'user',
            'user_info',
            'roles_licenses',
            'is_disabled',
            'created_on',
            'updated_on',
            # 'organization',
            'document_url',
        )

    def validate_user(self, value):
        qs = self.context['view'].get_queryset()
        if qs.filter(user_id=value).exists():
            raise serializers.ValidationError("user already exist.")
        return value


class OrganizationUserRoleNestedSerializer(NestedModelSerializer, serializers.ModelSerializer):
    """
    This defines organization role serializer.
    """
    # organization_user = OrganizationUserRoleRelatedField(
    #     queryset=OrganizationUser.objects.all(),
    # )
    # # organization_user_info = OrganizationUserNestedViewSerializer(source='organization_user', read_only=True)
    role = OrganizationUserRoleRelatedField(
        queryset=OrganizationRole.objects.all(),
    )
    # role_info = OrganizationRoleSerializer(source='role', read_only=True)
    licenses = OrganizationUserRoleRelatedField(
        queryset=License.objects.all(),
        many=True,
        # required=True,
    )

    def validate_licenses(self, value):
        """
        Check that license is selected.
        """
        if not value:
            raise serializers.ValidationError("At leat one License must be selected.")
        return value

    class Meta:
        model = OrganizationUserRole
        fields = (
            'id',
            # 'organization_user',
            # 'organization_user_info',
            'role',
            # 'role_info',
            'licenses',
            'created_on',
            'updated_on',
            # 'organization',
        )

############################### my-perm ################################
class myOrganizationRoleSerializer(NestedModelSerializer, serializers.ModelSerializer):
    """
    This defines organization role serializer.
    """

    class Meta:
        model = OrganizationRole
        fields = (
            "name",
            "permissions",
        )

class MyOrganizationRoleSerializer(OrganizationUserRoleNestedSerializer):
    role_info = myOrganizationRoleSerializer(source='role', read_only=True)
    class Meta:
        model = OrganizationUserRole
        fields = (
            # 'id',
            # 'organization_user',
            # 'organization_user_info',
            # 'role',
            'role_info',
            'licenses',
            # 'created_on',
            # 'updated_on',
            # 'organization',
        )

# class OrganizationUserRoleSerializer(serializers.ModelSerializer):
#     """
#     This defines organization role serializer.
#     """
#     # role_info = OrganizationRoleSerializer(source='role', read_only=True)
#     licenses = OrganizationUserRoleRelatedField(
#         queryset=License.objects.all(),
#         many=True,
#     )
#     class Meta:
#         model = OrganizationUserRole
#         fields = (
#             'id',
#             'role',
#             # 'role_info',
#             'licenses',
#             # 'created_on',
#             # 'updated_on',
#             # 'organization',
#         )




# class OrganizationUserSerializer(serializers.ModelSerializer):
#     """
#     This defines organization role serializer.
#     """
#     user_info = OrganizationUserInfoSerializer(source='user', read_only=True)
#     roles = OrganizationUserRoleSerializer(source='organization_user_role', many=True, read_only=True)
#     class Meta:
#         model = OrganizationUser
#         fields = (
#             'id',
#             'user',
#             'user_info',
#             'roles',
#             # 'created_on',
#             # 'updated_on',
#             # 'organization',
#         )


# class OrganizationRoleNestedSerializer(serializers.ModelSerializer):
#     """
#     This defines organization role serializer.
#     """

#     class Meta:
#         model = OrganizationRole
#         fields = (
#             'id',
#             'name',
#             'permissions',
#             # 'created_on',
#             # 'updated_on',
#             # 'organization',
#         )


class OrganizationDetailSerializer(OrganizationSerializer):
    """
    This defines ProgramOverviewSerializer
    """
    created_by = OrganizationUserInfoSerializer(read_only=True)
    # roles = OrganizationRoleNestedSerializer(many=True, read_only=True)
    # users = OrganizationUserSerializer(source='organization_user', many=True, read_only=True)
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        read_only_fields = ('id', 'created_by', 'created_on', 'updated_on')
        fields = (
            'id',
            'name',
            'profile_image_url',
            'email',
            'phone',
            'category',
            'about',
            'created_by',
            # 'roles',
            # 'users',
            # 'licenses',
            'ethics_and_certifications',
            'created_on',
            'updated_on',
        )

    def get_profile_image_url(self, obj):
        """
        Return s3 document url.
        """
        try:
            document = Documents.objects.filter(object_id=obj.id, doc_type='profile_image').latest('created_on')
            if document.box_url:
                return document.box_url
            else:
                path = document.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None


class InviteUserSerializer(NestedModelSerializer, serializers.ModelSerializer):
    """
    This defines Brand serializer.
    """

    # full_name = serializers.CharField(max_length=200)
    phone = PhoneNumberField(max_length=15)
    # email = serializers.EmailField()
    roles = InviteUserRelatedField(
        queryset=OrganizationRole.objects.all(),
        many=True,
        required=True,
    )
    license = InviteUserRelatedField(
        queryset=License.objects.all(),
    )

    # def validate_phone(self, value):
    #     """
    #     nonfield validation.
    #     """
    #     try:
    #         user = User.objects.get(phone=self.initial_data['phone'])
    #         if user.email != self.initial_data['email']:
    #             raise serializers.ValidationError("Phone number already in usefor another account.")
    #     except User.DoesNotExist:
    #         pass
    #     return value

    def create(self, validated_data):
        view = self.context['view']
        validated_data['created_by'] = view.request.user
        return super().create(validated_data)

    class Meta:
        model = LicenseUserInvite
        read_only_fields = ('id', 'status', 'is_invite_accepted',)
        fields = (
            'id',
            'full_name',
            'email',
            'phone',
            'roles',
            'license',
            'is_invite_accepted',
            'status',
            'created_on',
            'updated_on',
            # 'organization',
        )


class InviteUserVerificationSerializer(serializers.Serializer):
    """
    This defines serializer.
    """
    token = InviteUserTokenField()

    class Meta:
        fields = (
            'token',
        )

class OTPSerializer(serializers.Serializer):
    """
    This defines serializer.
    """
    otp = serializers.CharField(min_length=6, max_length=8)

    class Meta:
        fields = (
            'otp',
        )

    def validate_otp(self, value):
        if not value:
            raise serializers.ValidationError('OTP is required.')
        try:
            return int(value)
        except ValueError:
            raise serializers.ValidationError('OTP must be integer value')
        else:
            return value

class OnboardingDataFetchSerializer(serializers.ModelSerializer):
    """
    This defines serializer.
    """
    class Meta:
        model = OnboardingDataFetch
        read_only_fields = ('data_fetch_token', 'owner_verification_status', 'data_fetch_status', 'owner_email', 'owner_name')
        fields = (
            'data_fetch_token',
            'license_number',
            'owner_verification_status',
            'data_fetch_status',
            'owner_email',
            'owner_name',
        )

    def validate_license_number(self, value):
        if not value:
            raise serializers.ValidationError('license_number is required.')
        if License.objects.filter(license_number=value).exists():
            raise serializers.ValidationError(f'license {value} already in system.')
        else:
            return value
