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
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email','first_name', 'last_name','categories', 'full_name','country','state','date_of_birth','city','zip_code','phone','date_joined','legal_business_name','business_dba','existing_member','password', 'is_superuser', 'is_staff','status', 'step')
    

    def validate_password(self, password):
        if password:
            default_validate_password(password)
        return password

    
    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
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

    def get_encrypted_data(self, email):
        raw = pad(email)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = base64.urlsafe_b64encode(iv + cipher.encrypt(raw))
        return '{}reset-password?code={}'.format(settings.FRONTEND_DOMAIN_NAME, cipher_text.decode('ascii'))    


    
class ResetPasswordSerializer(PasswordSerializer):  # pylint: disable=W0223
    """
    Serializer for requesting a password reset e-mail.
    """
    code = serializers.CharField(max_length=255)

    def get_decrypted_data(self, enc):
        enc = base64.urlsafe_b64decode(enc)
        iv = enc[:BS]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc[BS:]))

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                "Passwords do not match")
        decoded_data = self.get_decrypted_data(data.get('code'))
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
