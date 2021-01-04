from rest_framework import serializers
from .models import OrganizationUserInvite
from .exceptions import (InvalidInviteToken, ExpiredInviteToken)

class NestedModelSerializer:
    """
    This defines Brand serializer.
    """
    def create(self, validated_data):
        view = self.context['view']
        if hasattr(view , 'get_parents_query_dict'):
            parents_query_dict = view.get_parents_query_dict(**view.kwargs)
            for key, value in parents_query_dict.items():
                validated_data[key+'_id'] = value
        return super().create(validated_data)


class OrganizationUserRoleRelatedField(serializers.RelatedField):

    def to_representation(self, obj):
        return obj.pk

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get(pk=data)
        except queryset.model.DoesNotExist:
            raise serializers.ValidationError(
            f'{queryset.model._meta.verbose_name} id {data} does not exist or you do not have access.'
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(organization=self.context.get('organization'))
        return queryset


class InviteUserRelatedField(serializers.RelatedField):

    def to_representation(self, obj):
        return obj.pk

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get(pk=data)
        except queryset.model.DoesNotExist:
            raise serializers.ValidationError(
            f'{queryset.model._meta.verbose_name} id {data} does not exist or you do not have access.'
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(organization=self.context.get('organization'))
        return queryset


class InviteUserTokenField(serializers.Field):

    def to_representation(self, obj):
        return obj.get_invite_token()

    def to_internal_value(self, data):
        try:
            instance = OrganizationUserInvite.get_object_from_invite_token(data)
        except ExpiredInviteToken:
                    raise serializers.ValidationError('Expired.')
        except InvalidInviteToken:
                    raise serializers.ValidationError('Invalid.')
        else:
            return instance