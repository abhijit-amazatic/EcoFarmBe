from rest_framework.permissions import BasePermission
from rest_framework.viewsets import ViewSetMixin
from django.views.generic import View
from django.utils.translation import ugettext_lazy as _
from permission.views_permission_base import ViewPermission


class LicenseViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_license',
        },
        'create': {
            'post': 'add_license',
        },
        'update': {
            'put': 'edit_license',
        },
        'partial_update': {
            'patch': 'edit_license',
        },
        'destroy': {
            'delete':'delete_license',
        },
        'existing_user_data_status': {
            'get': 'view_license',
        },
        'profile_contact': {
            'get': 'view_profile_contact',
            'patch': 'edit_profile_contact',
        },
        'cultivation_overview': {
            'get': 'view_cultivation_overview',
            'patch': 'edit_cultivation_overview',
        },
        'financial_overview': {
            'get': 'view_financial_overview',
            'patch': 'edit_financial_overview',
        },
        'crop_overview': {
            'get': 'view_crop_overview',
            'patch': 'edit_crop_overview',
        },
        'program_overview': {
            'get': 'view_program_overview',
            'patch': 'edit_program_overview',
        },
        'billing_information': {
            'get': 'view_billing_information',
            'patch': 'edit_billing_information',
        },
        'license_profile': {
            'get': 'view_license_profile',
            'patch': 'edit_license_profile',
        },
        'buyer_summary': {
            'get': 'view_license',
            'patch': 'edit_license',
        },
    }


class OrganizationViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_organization',
        },
        'create': {
            'post': 'add_organization',
        },
        'update': {
            'put': 'edit_organization',
        },
        'partial_update': {
            'patch': 'edit_organization',
        },
        'destroy': {
            'delete':'delete_organization',
        },
    }

class BrandViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_brand',
        },
        'create': {
            'post': 'add_brand',
        },
        'update': {
            'put': 'edit_brand',
        },
        'partial_update': {
            'patch': 'edit_brand',
        },
        'destroy': {
            'delete':'delete_brand',
        },
    }

class OrganizationRoleViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_organization_role',
        },
        'create': {
            'post': 'add_organization_role',
        },
        'update': {
            'put': 'edit_organization_role',
        },
        'partial_update': {
            'patch': 'edit_organization_role',
        },
        'destroy': {
            'delete':'delete_organization_role',
        },
    }

class OrganizationUserViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_organization_user',
        },
        'create': {
            'post': 'add_organization_user',
        },
        'update': {
            'put': 'edit_organization_user',
        },
        'partial_update': {
            'patch': 'edit_organization_user',
        },
        'destroy': {
            'delete':'delete_organization_user',
        },
    }

class OrganizationUserRoleViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_organization_user_role',
        },
        'create': {
            'post': 'add_organization_user_role',
        },
        'update': {
            'put': 'edit_organization_user_role',
        },
        'partial_update': {
            'patch': 'edit_organization_user_role',
        },
        'destroy': {
            'delete':'delete_organization_user_role',
        },
    }
