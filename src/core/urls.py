"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import (url, include,)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.views.static import serve
from rest_framework.routers import SimpleRouter

from core.admin_sites import logger_admin_site

router = SimpleRouter()


urlpatterns = [
    path('admin/', admin.site.urls),
    path('logger/', logger_admin_site.urls),
    path('', include('knoxpasswordlessdrf.urls')),

    path(r'', include('two_factor.urls')),
    path(r'', include('user.urls')),
    path(r'', include('brand.urls')),
    path(r'', include('internal_onboarding.urls')),
    path(r'', include('compliance_binder.urls')),
    path(r'', include('inventory.urls')),
    path(r'', include('integration.urls')),
    path(r'', include('fee_variable.urls')),
    path(r'', include('cultivar.urls')),
    path(r'', include('labtest.urls')),
    path(r'', include('bill.urls')),
    path(r'', include('permission.urls')),
    path(r'seo/', include('seo.urls')),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),

] + router.urls


if not settings.DEBUG:
    urlpatterns += [
        url(r'^static\/(?P<path>.*)$', serve,
            {'document_root': settings.STATIC_ROOT})
    ]
