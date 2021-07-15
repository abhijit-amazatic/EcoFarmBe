from django.contrib import admin
from drf_api_logger.models import APILogsModel
from drf_api_logger.admin import APILogsAdmin

class LoggerAdminSite(admin.AdminSite):
    site_header = "Logger admin"
    site_title = "Logger Admin Portal"
    index_title = "Welcome to Logger Admin"

logger_admin_site = LoggerAdminSite(name='logger_admin')


logger_admin_site.register(APILogsModel, APILogsAdmin)
if admin.site.is_registered(APILogsModel):
    admin.site.unregister(APILogsModel)