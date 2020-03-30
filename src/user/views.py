# """
# All views related to the User defined here.
# """
# import json
# from rest_framework import (status,)
# from rest_framework.permissions import (AllowAny, IsAuthenticated, )
# from rest_framework.response import Response
# from rest_framework.viewsets import (ModelViewSet,)
# from rest_framework.views import APIView
# from rest_framework.generics import GenericAPIView

# from knox.models import AuthToken
# from knox.settings import knox_settings

# from core.permissions import UserPermissions
# from .models import User
# from .serializers import (UserSerializer)


# from core.permissions import IsAuthenticatedSitePermission

# KNOXUSER_SERIALIZER = knox_settings.USER_SERIALIZER

# class UserViewSet(ModelViewSet):
#     """
#     User view set used for CRUD operations.
#     """
#     permission_classes = (UserPermissions,)

#     def get_queryset(self):
#         query_set = User.objects.filter(is_active=True)
#         if self.request.user.is_superuser:
#             return query_set
#         return query_set.filter(email=self.request.user)

#     def get_serializer_class(self):
#         if self.action == 'create':
#             return CreateUserSerializer
#         return UserSerializer

#     def create(self, request):
#         """
#         This view is  used to create user.
#         """
#         serializer = CreateUserSerializer(
#             data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         instance.is_active = False
#         instance.save()
#         return Response(status=status.HTTP_204_NO_CONTENT)

