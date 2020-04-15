"""
Integration views
"""
from rest_framework import (status,)
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
    permission_classes = (AllowAny,)

    def get(self, request):
        tokens = get_box_tokens()
        return Response(tokens)