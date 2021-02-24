from .settings import *


REST_KNOX = {
    'SECURE_HASH_ALGORITHM': 'cryptography.hazmat.primitives.hashes.SHA512',
    'AUTH_TOKEN_CHARACTER_LENGTH': 64,
    'TOKEN_TTL': None,  # None for never exp. token
    'USER_SERIALIZER': 'knox.serializers.UserSerializer',
}

# REST_FRAMEWORK = {
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticated',
#     ),
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'knox.auth.TokenAuthentication',
#         #'rest_framework.authentication.SessionAuthentication',
#     ),
#     'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
#     'DEFAULT_PAGINATION_CLASS': 'core.pagination.PageNumberPagination',
#     'PAGE_SIZE': 50,
#     'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.OrderingFilter', 'rest_framework.filters.SearchFilter',
#                                 'django_filters.rest_framework.DjangoFilterBackend',),
#     'ORDERING_PARAM': 'order-by',
#     'SEARCH_PARAM': 'q',
# }

AUTHENTICATION_BACKENDS = (
    # 'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
    'permission.backends.CustomPermissionBackend',
)
