"""
User related serializers defined here.
Basically they are used for API representation & validation.
"""
# import hashlib
# import base64
# from django.conf import settings
# from django.contrib.auth.password_validation import validate_password as default_validate_password
# from django.contrib.auth import (authenticate, login)
# from rest_framework import serializers
# from Crypto.Cipher import AES
# from Crypto import Random
# from .models import User


# BS = 16
# key = hashlib.md5(str('asdsadsadsds').encode('utf-8')).hexdigest()[:BS]


# def pad(s):
#     """
#     to adding padding in string for encryption purpose
#     """
#     return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)


# def unpad(s):
#     """
#     to remove padding in string for decryption purpose
#     """
#     return s[:-ord(s[len(s) - 1:])]



# class UserSerializer(serializers.ModelSerializer):
#     """
#     User Serializer.
#     """
#     id = serializers.ReadOnlyField()
#     email = serializers.EmailField(required=True)
#     password = serializers.CharField(
#         write_only=True,
#         required=False,
#         help_text='Leave empty if no change needed',
#         style={'input_type': 'password', 'placeholder': 'Password'}
#     )
#     is_staff = serializers.ReadOnlyField()
#     is_superuser = serializers.ReadOnlyField()
#     date_joined = serializers.ReadOnlyField()
    
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'email',
#                   'mobile_number', 'date_joined', 'password', 'is_superuser', 'is_staff')
    

#     def validate_password(self, password):
#         if password:
#             default_validate_password(password)
#         return password


#     def update(self, instance, validated_data):
#         user = super().update(instance, validated_data)
#         password = validated_data.get('password', None)
#         if user.check_password(password):
#             user.set_password(password)
#             user.save()
#         return user


# class CreateUserSerializer(UserSerializer):
#     """
#     Serializer to create user.
#     """  
#     def create(self, validated_data):
#         user = super().create(validated_data)
#         user.set_password(user.password)
#         user.save()
#         return user




    
