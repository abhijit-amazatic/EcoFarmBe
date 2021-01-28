"""
User related serializers defined here.
Basically they are used for API representation & validation.
"""
import binascii
from django.contrib.auth import (authenticate, login, get_user_model)
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField

from user.models import (User, PrimaryPhoneTOTPDevice,)

from .abstract_models import AbstractDevice as Device
from .models import (
    TwoFactorLoginToken,
    PhoneTOTPDevice,
    AuthyUser,
    AuthyAddUserRequest,
    AuthenticatorTOTPDevice,
    StaticDevice,
    StaticToken,
    AddAuthenticatorRequest,
)
from .conf import settings


User = get_user_model()

username_field = User.USERNAME_FIELD if hasattr(User, 'USERNAME_FIELD') else 'username'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (username_field, 'is_2fa_enabled')


class EmptySerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer.
    """
    pass

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
            raise serializers.ValidationError(
                'Email not confirmed! '
                + 'Please click the confirmation link sent your registered email.'
            )
        else:
            try:
                email = data.get('email')
                password = data.get('password')
                user = authenticate(email=email, password=password)
                login(self.context['request'], user, backend='django.contrib.auth.backends.ModelBackend')
                return user
            except Exception:
                raise serializers.ValidationError('Invalid Email or Password.')


class TwoFactorLoginDevicesSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for users two factor devices.
    """
    name = serializers.CharField(max_length=255)
    device_id = serializers.CharField(max_length=255)
    type = serializers.CharField(max_length=255)
    is_interactive = serializers.BooleanField()
    challenge_methods = serializers.ListField()

class TwoFactorDevicesSerializer(TwoFactorLoginDevicesSerializer):
    """
    Serializer for users two factor devices.
    """
    confirmed = serializers.BooleanField(read_only=True)
    is_removable = serializers.BooleanField(read_only=True)
    phone_number = PhoneNumberField(read_only=True)
    app_device_name = serializers.CharField(read_only=True)
    created_on = serializers.DateTimeField(read_only=True)
    updated_on = serializers.DateTimeField(read_only=True)

class DeviceIdSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for persistent id of users two factor device.
    """
    device_id = serializers.CharField(max_length=255)

    def validate_device_id(self, value):
        device = Device.from_device_id(value)
        if not device:
            raise serializers.ValidationError("invalid device_id")
        user = self.context['request'].user
        if not user.is_authenticated  or value not in user.get_two_factor_device_dict():
            raise serializers.ValidationError("Device not accessible")
        setattr(self, 'device', device)
        return value


class TwoFactorDevicesChallengeSerializer(DeviceIdSerializer): # pylint: disable=W0223
    """
    Serializer for users two factor devices interaction.
    """
    challenge_method = serializers.CharField(max_length=255, required=False)

    def validate(self, attrs):
        """
        Check that start is before finish.
        """
        data = super().validate(attrs)
        if self.device.challenge_methods and 'challenge_method' in data:
            method = data['challenge_method']
            if method not in self.device.challenge_methods:
                raise serializers.ValidationError(
                    {'challenge_method': [f"{method} method not supported"]},
                )
        return data

class TwoFactorDevicesChallengeMethodSerializer(serializers.Serializer): # pylint: disable=W0223
    """
    Serializer for users two factor devices interaction.
    """
    challenge_method = serializers.CharField(max_length=255, required=False)

    def validate_challenge_method(self, value):
        """
        Check that start is before finish.
        """
        if self.instance.challenge_methods and value:
            if value not in self.instance.challenge_methods:
                raise serializers.ValidationError(f"method {value} is not supported")
        return value

class TokenSerializer(serializers.Serializer): # pylint: disable=W0223
    """
    Serializer for token.
    """
    token = serializers.CharField(max_length=255, required=False,)

class TwoFactorLogInVerificationSerializer(TokenSerializer, DeviceIdSerializer): # pylint: disable=W0223
    """
    Serializer for users two login.
    """
    pass


class AuthyAddUserRequestSerializer(serializers.ModelSerializer):
    """
    Add Authy user request serializer
    """

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        try:
            add_user_request = AuthyAddUserRequest.objects.get(user=user)
            add_user_request.delete()
        except AuthyAddUserRequest.DoesNotExist:
            pass

        return super().create(validated_data)

    class Meta:
        model = AuthyAddUserRequest
        fields = ('request_id', 'issued_at', 'expire_at', 'status')
        read_only_fields = ('request_id', 'issued_at', 'expire_at', 'status')

class AddPhoneDeviceSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for requesting verification SMS
    """
    phone_number = PhoneNumberField(max_length=15)

    def validate(self, data):
        user = self.context['request'].user
        if user.phone == data['phone_number']:
            raise serializers.ValidationError({'phone_number': 'Already in use as a primary number'})
        if PhoneTOTPDevice.objects.filter(user=user, phone_number=data['phone_number']).first():
            raise serializers.ValidationError({'phone_number': 'Already exist'})
        return data

class AddAuthenticatorRequestSerializer(serializers.ModelSerializer):
    """
    Add Authy user request serializer
    """

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        try:
            add_user_request = AddAuthenticatorRequest.objects.get(user=user)
        except AddAuthenticatorRequest.DoesNotExist:
            pass
        else:
            add_user_request.delete()

        return super().create(validated_data)

    class Meta:
        model = AddAuthenticatorRequest
        fields = ('request_id', 'issued_at', 'expire_at', 'status')
        read_only_fields = ('request_id', 'issued_at', 'expire_at', 'status')
