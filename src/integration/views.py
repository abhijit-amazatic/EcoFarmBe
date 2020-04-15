"""
Integration views
"""
from rest_framework import (status,)
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import UserPermissions
from .models import Integration
from integration.box import(get_box_tokens, )


class GetBoxTokensView(APIView):
    """
    Return Access and Refresh Tokens for Box.
    """
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tokens = get_box_tokens()
        return Response(tokens)