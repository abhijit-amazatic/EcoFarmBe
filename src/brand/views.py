# pylint:disable = all
"""
This module defines API views.
"""

import json
from rest_framework.response import Response
from rest_framework import (permissions, viewsets, status, filters,)
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django.conf import settings
from core.permissions import IsAuthenticatedBrandPermission
from .models import (Brand,ProfileCategory, )

class ProfileCategoryView(APIView):

    """
    Get ProfileCategories information.
    """
    permission_classes = (permissions.AllowAny,)
    
    def get(self, request):
        """
        Display categories.    
        """
        queryset = ProfileCategory.objects.values('id','name')
        return Response(queryset)


