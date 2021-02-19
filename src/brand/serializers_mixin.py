from rest_framework import serializers
from permission.filterqueryset import (filterQuerySet,)
from .exceptions import (InvalidInviteToken, ExpiredInviteToken)
from .models import (
    License,
    Brand,
    OrganizationUserInvite,
    OrganizationRole,
)

class NestedModelSerializer:
    """
    This defines Brand serializer.
    """
    # def create(self, validated_data):
    #     view = self.context['view']
    #     if hasattr(view , 'get_parents_query_dict'):
    #         parents_query_dict = view.get_parents_query_dict(**view.kwargs)
    #         for key, value in parents_query_dict.items():
    #             validated_data[key+'_id'] = value
    #     return super().create(validated_data)

    def create(self, validated_data):
        parent_field_default = self.context.get('parent_field_default')
        if parent_field_default:
            validated_data.update(parent_field_default)
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

class OrganizationRoleInfoSerializer(serializers.ModelSerializer):
    """
    This defines organization role serializer.
    """

    class Meta:
        model = OrganizationRole
        fields = (
            'id',
            'name',
        )

class OrganizationUserRoleRelatedRoleField(OrganizationUserRoleRelatedField):
    def to_representation(self, obj):
        return OrganizationRoleInfoSerializer(obj).data

class LicenseInfoSerializer(serializers.ModelSerializer):
    """
    This defines organization role serializer.
    """

    class Meta:
        model = License
        fields = (
            'id',
            'license_number',
            'legal_business_name',
        )

class OrganizationUserRoleRelatedLicenseField(OrganizationUserRoleRelatedField):
    def to_representation(self, obj):
        return LicenseInfoSerializer(obj).data

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

class LicenseProfileBrandAssociationField(serializers.RelatedField):
    queryset=Brand.objects.all()

    def to_representation(self, obj):
        return obj.id

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            int(data)
        except ValueError:
            raise serializers.ValidationError(f'Error while parsing  brand id \'{data}\' as integer.')
        try:
            brand_obj = queryset.get(id=data)
        except Brand.DoesNotExist:
            raise serializers.ValidationError(
                f'Brand id \'{data}\' does not exist or you do not have access.')
        else:
            return brand_obj

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filterQuerySet.for_user(queryset, self.context['request'].user)
        return queryset
