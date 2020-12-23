"""
Custom storage backends.
"""
from storages.backends.s3boto3 import S3Boto3Storage
# Disabled pylint 'abstract-method' warning for all storageclasses
from django.conf import settings
# cause it is not implimeted in 'S3Boto3Storage' backend


class CKEditorMediaStorage(S3Boto3Storage):  # pylint: disable=abstract-method
    """
    Custom storage backends for public media files.
    """
    #location = settings.CKEDITOR_UPLOAD_PATH
    default_acl = 'public-read'
    file_overwrite = False

    
# class StaticStorage(S3Boto3Storage):  # pylint: disable=abstract-method
#     """
#     Custom storage backends for static files.
#     """
#     location = settings.STATIC_LOCATION
#     default_acl = 'public-read'
    
    
# class PrivateMediaStorage(S3Boto3Storage):  # pylint: disable=abstract-method
#     """
#     Custom storage backends for private media files.
#     """
#     location = 'private'
#     default_acl = 'private'
#     object_parameters = getattr(
#         settings, 'PRIVATE_MEDIA_AWS_S3_OBJECT_PARAMETERS',
#         {'CacheControl': 'max-age=600'},
#     )
#     querystring_expire = getattr(
#         'settings', 'PRIVATE_MEDIA_AWS_QUERYSTRING_EXPIRE',
#         600,
#     )
#     default_acl = 'private'
#     file_overwrite = True
#     custom_domain = False
