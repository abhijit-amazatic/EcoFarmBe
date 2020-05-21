"""
This module defines API views.
"""
import json
from rest_framework.response import Response
from rest_framework import (permissions, viewsets, status, filters,) 
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.decorators import action
from .serializers import (AccountSerializer,AccountCreateSerializer, AccountLicenseSerializer, AccountBasicProfileSerializer, AccountContactInfoSerializer,)
from .models import (Account,AccountUser,AccountLicense, AccountBasicProfile, AccountContactInfo, )
from core.permissions import IsAuthenticatedAccountPermission
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound


class AccountViewSet(viewsets.ModelViewSet):
    """
    All Account related endpoint's view is defined here.
    """
    permission_classes = (IsAuthenticatedAccountPermission, )
    filter_backends = [filters.SearchFilter]
    search_fields = ['account_category', ]
    basic_profile_path = 'basic-profile(/(?P<basic_profile_id>[0-9]*))?'
    contact_info_path = 'contact-info(/(?P<contact_info_id>[0-9]*))?'

    def get_serializer_class(self):
        """
        Return serializer on the basis of action.
        """
        if self.action == 'create':
            return AccountCreateSerializer
        elif self.action == 'basic_profile':
            return AccountBasicProfileSerializer
        elif self.action == 'contact_info':
            return AccountContactInfoSerializer
        return AccountSerializer


    def get_queryset(self):
        """
        Return queryset based on action.
        """
        accounts = Account.objects.filter()
        if self.action == "list":
            accounts = accounts.select_related('ac_manager')
        elif self.action == "basic_profile":
            accounts = accounts.select_related('account_profile')
        elif self.action =="contact_info":
            accounts = accounts.select_related('account_contact')
        if not self.request.user.is_staff and not self.request.user.is_superuser:
            accounts = accounts.filter(account_roles__user=self.request.user)
        return accounts

    def create(self, request):
        """
        This endpoint is used to create Account.
        """
        #when account is added here add users entry to accountuser
        serializer = AccountCreateSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            try:
                accounts = Account.objects.filter(ac_manager_id=request.data.get('ac_manager'))
                for account in accounts:
                    if not AccountUser.objects.filter(user=request.data.get('ac_manager'), account=account.id).exists():
                        AccountUser.objects.create(user_id=request.data.get('ac_manager'),account_id=account.id,role='owner')
            except Exception as e:
                print(e)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def extra_info(self, request, pk, model, serializer, extra_info_attribute):
        """
        Generic feature for detail route.
        """
        account = self.get_object()
        if request.method == 'GET':
            try:
                return Response(serializer(
                    getattr(account, extra_info_attribute)).data)
            except model.DoesNotExist:
                return Response({})
        else:
            try:
                ser = serializer(
                    getattr(account, extra_info_attribute), data=request.data,context={'request': request},partial=True)
            except model.DoesNotExist:
                request.data['account'] = account.id
                ser = serializer(data=request.data, context={'request': request})
            ser.is_valid(raise_exception=True)
            ser.save(account=account)
            return Response(ser.data)

    @action(detail=True, url_path=basic_profile_path, methods=['get','patch'])
    def basic_profile(self, request, pk,basic_profile_id=None):
        """
        Detail route CRUD operations on basic_profile.
        """
        return self.extra_info(request, pk, AccountBasicProfile,AccountBasicProfileSerializer, 'account_profile')
        

    @action(detail=True, url_path=contact_info_path, methods=['get','patch'])
    def contact_info(self, request, pk,contact_info_id=None):
        """
        Detail route CRUD operations on contact_info.
        """
        return self.extra_info(request, pk, AccountContactInfo, AccountContactInfoSerializer, 'account_contact')

    
class AccountLicenseViewSet(viewsets.ModelViewSet):
    """
    All Account related license data stored here.
    """
    serializer_class = AccountLicenseSerializer
    permission_classes = (IsAuthenticatedAccountPermission, )
    filter_backends = [filters.SearchFilter]
    search_fields = ['legal_business_name', ]
    
    
    def get_queryset(self):
        """
        Return queryset based on action.
        """
        licenses = AccountLicense.objects.filter()
        if self.action == "list":
            licenses = licenses.select_related('account')
        if not self.request.user.is_staff and not self.request.user.is_superuser:
            licenses = licenses.filter(account__account_roles__user=self.request.user)
        return licenses

    def create(self, request):
        """
        This endpoint is used to create Account Licensse.
        """
        serializer = AccountLicenseSerializer(data=request.data, context={'request': request}, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
