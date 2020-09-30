"""
User related serializers defined here.
Basically they are used for API representation & validation.
"""
import binascii
from django.contrib.auth import (authenticate, login)
from rest_framework import serializers

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
)
from .conf import settings


class EmptySerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer.
    """


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
                login(self.context['request'], user)
                return user
            except Exception:
                raise serializers.ValidationError('Invalid Email or Password.')


class TwoFactorDevicesSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer for users two factor devices.
    """
    name = serializers.CharField(max_length=255)
    device_id = serializers.CharField(max_length=255)
    type = serializers.CharField(max_length=255)
    is_interactive = serializers.BooleanField()
    challenge_methods = serializers.ListField()

    # def get_device_id(self, obj):
    #     return binascii.hexlify(obj.persistent_id.encode('utf-8'))


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


class TwoFactorLogInVerificationSerializer(DeviceIdSerializer): # pylint: disable=W0223
    """
    Serializer for users two login.
    """
    token = serializers.CharField(max_length=255, required=False,)



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
