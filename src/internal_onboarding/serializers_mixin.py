from rest_framework import serializers
from .exceptions import (InvalidInviteToken, ExpiredInviteToken)
from .models import (
    InternalOnboardingInvite
)


class InternalOnboardingInviteTokenField(serializers.Field):

    def to_representation(self, obj):
        return obj.get_invite_token()

    def to_internal_value(self, data):
        try:
            instance = InternalOnboardingInvite.get_object_from_invite_token(data)
        except ExpiredInviteToken:
                    raise serializers.ValidationError('Expired token.')
        except InvalidInviteToken:
                    raise serializers.ValidationError('Invalid token.')
        else:
            return instance
