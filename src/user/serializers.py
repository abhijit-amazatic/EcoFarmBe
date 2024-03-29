"""
User related serializers defined here.
Basically they are used for API representation & validation.
"""
import hashlib
import base64
from logging import exception
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password as default_validate_password
from django.contrib.auth import (authenticate, login)
from core.settings import (AWS_BUCKET, )
from rest_framework import serializers
from Crypto.Cipher import AES
from Crypto import Random
from phonenumber_field.serializerfields import PhoneNumberField

from permission.models import InternalRole
from .models import User, TermsAndCondition, HelpDocumentation, NewsletterSubscription
from integration.box import (get_preview_url, )
from core.utility import send_async_user_approval_mail
from brand.models import (License, Organization)
from inventory.models import (Documents, )
from integration.apps.aws import (create_presigned_url, )

from two_factor.serializers import TwoFactorDevicesSerializer
from brand.serializers import OrganizationSerializer
from permission.filterqueryset import filterQuerySet

BS = 16
key = hashlib.md5(str('asdsadsadsds').encode('utf-8')).hexdigest()[:BS]


def pad(s):
    """
    to adding padding in string for encryption purpose
    """
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)


def unpad(s):
    """
    to remove padding in string for decryption purpose
    """
    return s[:-ord(s[len(s) - 1:])]


def get_encrypted_data(email, reason=None):
        raw = pad(email)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(bytes(key,'utf-8'),AES.MODE_CBC,iv)
        cipher_text = base64.urlsafe_b64encode(iv + cipher.encrypt(bytes(raw,'utf-8')))
        if reason == "forgot_password":
            return '{}reset-password?code={}'.format(settings.FRONTEND_DOMAIN_NAME, cipher_text.decode('ascii'))
        else:
           return '{}verify-user?code={}'.format(settings.FRONTEND_DOMAIN_NAME, cipher_text.decode('ascii'))

def get_decrypted_data(enc):
        enc = base64.urlsafe_b64decode(enc)
        iv = enc[:BS]
        #cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher = AES.new(bytes(key,'utf-8'),AES.MODE_CBC,iv)
        return unpad(cipher.decrypt(enc[BS:]))       


class UserSerializer(serializers.ModelSerializer):
    """
    User Serializer.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        help_text='Leave empty if no change needed',
        style={'input_type': 'password', 'placeholder': 'Password'}
    )
    organizations = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    internal_roles = serializers.SerializerMethodField()
    internal_permission = serializers.SerializerMethodField()
    member_categories = serializers.SerializerMethodField()
    two_factor_devices = serializers.SerializerMethodField()
    platform_kpi = serializers.SerializerMethodField()

    def get_organizations(self, obj):
        """
        Return s3 document url.
        """
        qs = Organization.objects.all()
        qs = filterQuerySet.for_user(queryset=qs, user=obj)
        org_id_ls = list(qs.values_list('id', flat=True))
        if not obj.default_org_id in org_id_ls:
            try:
                def_org_id = int(settings.INTERNAL_USER_DEFAULT_ORG_ID)
            except Exception:
                obj.default_org = None
            else:
                if obj.internal_roles.all().exists() and def_org_id in org_id_ls:
                    obj.default_org_id = def_org_id
                else:
                    obj.default_org = None

            obj.save()

        serializer = OrganizationSerializer(qs, many=True, read_only=True)
        return serializer.data

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

    def get_internal_roles(self, obj):
        """
        Return perm list.
        """
        return [x.name for x in obj.internal_roles.all()]

    def get_internal_permission(self, obj):
        """
        Return perm list.
        """
        perm = set()
        for role in obj.internal_roles.all():
            for x in role.permissions.all():
                perm.add(x.id)
        return list(perm)

    def get_member_categories(self, obj):
        """
        Adds ,member categories to response
        """
        return obj.categories.values()

    def get_two_factor_devices(self, obj):
        """
        Adds Two factor devices
        """
        return TwoFactorDevicesSerializer(
            obj.get_two_factor_devices(confirmed_only=False),
            many=True,
        ).data

    def get_platform_kpi(self, obj):
        """
        Adds vendors profiles kpis for 'my platform' to the user/me response.
        """
        qs  = License.objects.all()
        qs = filterQuerySet.for_user(qs, obj)
        profile_count = qs.count()
        return {"profile_count":profile_count}

    class Meta:
        model = User
        read_only_fields = (
            'id',
            'is_staff',
            'is_superuser',
            'unique_user_id',
            'is_phone_verified',
            'crm_link',
            'date_joined',
            'is_verified',
            'is_2fa_enabled',
            'is_approved',
            'profile_photo_sharable_link',
            'approved_on',
            'approved_by',
            'created_on',
            'updated_on',
        )
        exclude = (
            'last_login',
            'is_active',
            'groups',
            'user_permissions',
            'bypass_terms_and_conditions',
            'zoho_crm_id',
            'zoho_contact_id',
            'is_updated_in_crm',
        )

    def validate_password(self, password):
        if password:
            default_validate_password(password)
        return password

    
    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        profile_photo_id = validated_data.get("profile_photo")
        try:
            if profile_photo_id:
                shared_url = get_preview_url(profile_photo_id)
                user.profile_photo_sharable_link = shared_url
                user.save()
        except Exception as e:
            print("Error while updating profile photo link.", e)
        password = validated_data.get('password', None)
        if user.check_password(password):
            user.set_password(password)
            user.save()
        return user


class CreateUserSerializer(UserSerializer):
    """
    Serializer to create user.
    """
    def validate_email(self, email):
        try:
            user = User.objects.get(  # noqa
                email=email)
            if user:
                raise serializers.ValidationError("Email address already exists!")
        except User.DoesNotExist:
            return email

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(user.password)
        user.save()
        return user

    
class LogInSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for login data.
    """
    email = serializers.CharField(style={'placeholder': 'Email'})
    password = serializers.CharField(
        style={'input_type': 'password', 'placeholder': 'Password'})

    def validate(self, data):
        try:
            get_user = User.objects.get(email=data.get('email'))
        except User.DoesNotExist:
            raise serializers.ValidationError("User Does Not Exist")
        if not get_user.is_verified:
            raise serializers.ValidationError('Email not confirmed!Please click the confirmation link sent your registered email.')
        else:    
            try:
                email = data.get('email')
                password = data.get('password')
                user = authenticate(email=email, password=password)
                login(self.context['request'], user, backend='django.contrib.auth.backends.ModelBackend')
                return user
            except Exception:
                raise serializers.ValidationError('Invalid Email or Password.')
        

class PasswordSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for default password fields.
    """
    new_password = serializers.CharField(required=True, max_length=30)
    confirm_password = serializers.CharField(required=True, max_length=30)
        

class ChangePasswordSerializer(PasswordSerializer):  # pylint: disable=W0223
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True, max_length=30)

    def validate(self, data):
        if not self.context['request'].user.check_password(data.get('old_password')):
            raise serializers.ValidationError(
                {'old_password': "Wrong password."})
        if data.get('confirm_password') != data.get('new_password'):
            raise serializers.ValidationError(
                {'password': "Two passwords didn't match."})
        return data

    def create(self, validated_data):
        user = User.objects.get(
            email=self.context['request'].user.email)
        user.set_password(validated_data.get('new_password'))
        user.save()
        return user

class SendMailSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for requesting a password reset e-mail.
    """
    email = serializers.EmailField()

    def validate_email(self, email):
        """
        Validation for email fields.
        """
        try:
            User.objects.get(  # noqa
                email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email address not found.")
        return email

    # def get_encrypted_data(self, email, reason=None):
    #     raw = pad(email)
    #     iv = Random.new().read(AES.block_size)
    #     cipher = AES.new(key, AES.MODE_CBC, iv)
    #     cipher_text = base64.urlsafe_b64encode(iv + cipher.encrypt(raw))
    #     if reason == "forgot_password":
    #         return '{}reset-password?code={}'.format(settings.FRONTEND_DOMAIN_NAME, cipher_text.decode('ascii'))
    #     else
    #        return '{}verify-user?code={}'.format(settings.FRONTEND_DOMAIN_NAME, cipher_text.decode('ascii'))

    
class ResetPasswordSerializer(PasswordSerializer):  # pylint: disable=W0223
    """
    Serializer for requesting a password reset e-mail.
    """
    code = serializers.CharField(max_length=255)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                "Passwords do not match")
        decoded_data = get_decrypted_data(data.get('code'))
        data['user'] = decoded_data.decode('ascii')
        return data

    def create(self, validated_data):
        try:
            user = User.objects.get(
                email=validated_data.get('user'))
        except User.DoesNotExist:
            raise serializers.ValidationError("User Does Not Exist")

        user.set_password(validated_data.get('new_password'))
        user.save()
        return user


class VerificationSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for requesting extracting & decoing code.
    """
    code = serializers.CharField(max_length=255)

    def validate(self, data):
        decoded_data = get_decrypted_data(data.get('code'))
        data['user'] = decoded_data.decode('ascii')
        return data

    def create(self, validated_data):
        try:
            user = User.objects.get(
                email=validated_data.get('user'))
        except User.DoesNotExist:
            raise serializers.ValidationError("User Does Not Exist")

        user.is_verified = True
        if user.is_phone_verified:
            user.is_approved = True
            user.approved_on = timezone.now()
            user.approved_by = {'email':"connect@thrive-society.com(Automated-Bot)"}
            send_async_user_approval_mail.delay(user.id)
        user.save()
        return user    

class SendVerificationSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for requesting verification link
    """
    email = serializers.CharField(max_length=255)
    

class PhoneNumberSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for requesting verification SMS
    """
    phone_number = PhoneNumberField(max_length=15)
 
 
class PhoneNumberVerificationSerializer(PhoneNumberSerializer):  # pylint: disable=W0223
    """
    Serializer for requesting extracting & decoing code.
    """
    code = serializers.CharField(min_length=6, max_length=6)


class TermsAndConditionAcceptanceSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for terms and condition acceptance,
    """
    # user_id = serializers.IntegerField(read_only=True)
    #profile_type = serializers.ChoiceField( choices=TermsAndCondition.PROFILE_TYPE_CHOICES)
    is_accepted = serializers.BooleanField()
    ip_address = serializers.IPAddressField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    hostname = serializers.CharField(read_only=True)
    created_on = serializers.CharField(read_only=True)

        
    def validate(self, value):
        qs = TermsAndCondition.objects.filter(
            profile_type='other',
            publish_from__lte=timezone.now().date(),
        )
        if qs.exists():
            setattr(self, 'tac_obj', qs.latest('publish_from'))
        else:
            raise serializers.ValidationError(f"Terms And Condition not found for profile type '{value}'")
        return value


class HelpDocumentationSerializer(serializers.ModelSerializer):
    """
    This defines HelpDocumentationSerializer
    """
    class Meta:
        model = HelpDocumentation
        fields = ('__all__')
    

class NewsletterSubscriptionSerializer(serializers.ModelSerializer):
    """
    This defines NewsletterSubscriptionSerializer
    """
    class Meta:
        model = NewsletterSubscription
        fields = ('__all__')
