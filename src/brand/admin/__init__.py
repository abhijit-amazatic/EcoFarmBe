from django.contrib import admin

from ..models import (
    Organization,
    Brand,
    License,
    ProfileContact,
    LicenseProfile,
    CultivationOverview,
    NurseryOverview,
    ProgramOverview,
    FinancialOverview,
    CropOverview,
    ProfileCategory,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
    LicenseUserInvite,
    OrganizationUserInvite,
)

from .brand_admin import (
    BrandAdmin,
)
from .license_admin import (
    LicenseAdmin,
)
from .organization_admin import (
    OrganizationAdmin,
    # OrganizationRoleAdmin,
)
from .user_invite_admin import (
    # OrganizationUserInviteAdmin,
    LicenseUserInviteAdmin,
)
from .profile_category_admin import (
    ProfileCategoryAdmin,
)

admin.site.register(Brand, BrandAdmin)
admin.site.register(Organization, OrganizationAdmin)
# admin.site.register(OrganizationRole,OrganizationRoleAdmin)
# admin.site.register(OrganizationUserInvite, OrganizationUserInviteAdmin)
admin.site.register(LicenseUserInvite, LicenseUserInviteAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(ProfileCategory, ProfileCategoryAdmin)
