"""
This module defines API views.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (AllowAny, IsAuthenticated, )

from .models import (
    PageMeta,
)
from .serializers import (
    PageMetaSerializer,
)


class PageMetaView(APIView):
    """
    Return Access and Refresh Tokens for Box.
    """
    permission_classes = (AllowAny, )

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get(self, request, *args, **kwargs):
        try:
            url = request.query_params.get('url')
            if not url:
                return Response({"detail": "Query parameter 'url' is required"}, status=400)
            instance = PageMeta.objects.get(page_url=url)
        except PageMeta.DoesNotExist:
            return Response({"detail": "Mata not found for this url"}, status=404)
        except Exception as exc:
            return Response({"detail": exc}, status=400)
        else:
            serializer = PageMetaSerializer(instance, context=self.get_serializer_context)
            return Response(serializer.data)
