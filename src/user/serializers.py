"""
User related serializers defined here.
Basically they are used for API representation & validation.
"""
import hashlib
import base64
from django.conf import settings
from django.contrib.auth.password_validation import validate_password as default_validate_password
from django.contrib.auth import (authenticate, login)
from rest_framework import serializers
from Crypto.Cipher import AES
from Crypto import Random
from .models import User
from vendor.models import Vendor, VendorProfile, VendorUser, ProfileContact, License
from account.models import Account, AccountUser,AccountLicense,AccountBasicProfile,AccountContactInfo
from vendor.serializers import VendorSerializer, VendorProfileSerializer
from integration.box import (get_preview_url, )

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
       



class VendorFromUserVendorSerializer(serializers.ModelSerializer):
    """
    Vendor users.
    """
    id = serializers.IntegerField(source="vendor.id")
    vendor_category = serializers.CharField(source="vendor.vendor_category")
    role_id = serializers.IntegerField(source="id")
   
    class Meta:
        model = VendorUser
        fields = (
            'id', 'role', 'role_id','vendor_category',)


        
class UserSerializer(serializers.ModelSerializer):
    """
    User Serializer.
    """
    id = serializers.ReadOnlyField()
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        help_text='Leave empty if no change needed',
        style={'input_type': 'password', 'placeholder': 'Password'}
    )
    is_staff = serializers.ReadOnlyField()
    is_superuser = serializers.ReadOnlyField()
    date_joined = serializers.ReadOnlyField()
    vendor_profiles = serializers.SerializerMethodField(read_only=True)
    associated_profile_names = serializers.SerializerMethodField(read_only=True)
    member_categories = serializers.SerializerMethodField(read_only=True)
    #vendors = serializers.SerializerMethodField(read_only=True)
    vendors = VendorFromUserVendorSerializer(
        source='user_roles', many=True, read_only=True
    )
    is_verified = serializers.ReadOnlyField()
    is_approved = serializers.ReadOnlyField()
    approved_on = serializers.ReadOnlyField()
    approved_by = serializers.ReadOnlyField()
    profile_photo_sharable_link = serializers.ReadOnlyField()
    platform_kpi = serializers.SerializerMethodField(read_only=True)
    accounts_kpi = serializers.SerializerMethodField(read_only=True)
    
    
    
    # def get_vendors(self, obj):
    #     """
    #     Adds vendors to the user/me response.
    #     """
    #     results = Vendor.objects.filter(ac_manager=obj).values('id','vendor_category','ac_manager')
    #     return results

    def get_member_categories(self, obj):
        """
        Adds ,member categories to response
        """
        return obj.categories.values()
    
    def get_vendor_profiles(self, obj):
        """
        Adds vendors profiles to the user/me response.
        """
        results = VendorProfile.objects.filter(vendor__vendor_roles__user=obj).values('id', 'status','step', 'vendor')
        return results

    def get_associated_profile_names(self, obj):
        """
        Returns farm name/s of vendors.
        """
        farms = []
        profiles = VendorProfile.objects.filter(vendor__vendor_roles__user=obj)
        if profiles:
            for profile in profiles:
                pc = ProfileContact.objects.filter(vendor_profile_id=profile.id)
                farm_names = [i.profile_contact_details.get('farm_name','') for i in pc]
                farms.extend(farm_names)
        return farms if farms else []

    def get_platform_kpi(self, obj):
        """
        Adds vendors profiles kpis for 'my platform' to the user/me response.
        """
        results = VendorProfile.objects.filter(vendor__vendor_roles__user=obj)
        return [{'profile_id':profile.id,
                 'status':profile.status,
                 'vendor_category':profile.vendor.vendor_category,
                 'farm_profile_photo':"N/A" if not hasattr(profile,'profile_contact') else profile.profile_contact.farm_profile_photo,
                 'farm_photo_sharable_link':"N/A" if not hasattr(profile,'profile_contact') else profile.profile_contact.farm_photo_sharable_link, 
                 'profile_name':profile.profile_name(),
                 'county': "N/A" if not hasattr(profile,'profile_contact') else profile.profile_contact.profile_contact_details.get('primary_county','N/A'),
                 'region':"N/A" if not hasattr(profile,'profile_contact') else profile.profile_contact.profile_contact_details.get('region','N/A'),
                 'cultivation_types':profile.profile_type,
                 'licenses_owned':License.objects.filter(vendor_profile=profile,owner_or_manager='owner').count(),
                 'licenses_managed':License.objects.filter(vendor_profile=profile,owner_or_manager='manager').count(),
                 'updated_on':profile.updated_on
        } for profile in results]
    
    def get_accounts_kpi(self, obj):
        """
        Adds account kpis for 'my platform' to the user/me response.
        """
        results = Account.objects.filter(account_roles__user=obj)#.values('id', 'status','step', 'account_category')
        return [{'account_id':account.id,
                 'status':account.status,
                 'step':account.step,
                 'account_category':account.account_category,
                 'brand_name':"N/A" if not hasattr(account,'account_profile') else account.account_profile.brand_name,
                 'county':"N/A" if not hasattr(account,'account_profile') else account.account_profile.county,
                 'region':"N/A" if not hasattr(account,'account_profile') else account.account_profile.region,
                 'licenses_owned':AccountLicense.objects.filter(account=account,owner_or_manager='owner').count(),
                 'licenses_managed':AccountLicense.objects.filter(account=account,owner_or_manager='manager').count(),
                 'updated_on':account.updated_on
        } for account in results]
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email','first_name', 'vendors', 'vendor_profiles','associated_profile_names','last_name','categories','member_categories','membership_type','full_name','country','state','date_of_birth','city','zip_code','phone','date_joined','legal_business_name','business_dba','existing_member','password', 'is_superuser', 'is_staff','is_verified', 'is_approved','status', 'step','profile_photo','profile_photo_sharable_link','title','department','website','instagram','linkedin','facebook','twitter','approved_on','approved_by','platform_kpi','accounts_kpi')
    

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
                login(self.context['request'], user)
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
        user.save()
        return user    

class SendVerificationSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for requesting verification link
    """
    email = serializers.CharField(max_length=255)
    
