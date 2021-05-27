from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, MethodNotAllowed
from .serializers_mixin import InternalOnboardingInviteTokenField



class InternalOnboardingInviteVerifySerializer(serializers.Serializer):
    """
    Password Retype Serializer to cross check password.
    """
    token = InternalOnboardingInviteTokenField()

    class Meta:
        fields = (
            'token',
        )


class InternalOnboardingInviteSetPassSerializer(serializers.Serializer):
    """
    Password Retype Serializer to cross check password.
    """
    token = InternalOnboardingInviteTokenField(required=True,)

    new_password = serializers.CharField(
        label="New Password",
        required=True,
        max_length=128,
        min_length=5,
        style={'input_type': 'password'},
    )
    confirm_password = serializers.CharField(
        label="Confirm New Password",
        required=True,
        max_length=128,
        min_length=5,
        style={'input_type': 'password'},
        write_only=True,
    )

    def validate_confirm_password(self, value):
        """
        Check current password.
        """
        if self.context['request'].data['password'] != value:
            raise serializers.ValidationError("Password does not match.")
        return value

    class Meta:
        fields = (
            'token',
            'new_password',
            'confirm_password',
        )
