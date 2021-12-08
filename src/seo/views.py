"""
This module defines API views.
"""
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework import (filters,)

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    PageMeta,
)
from .serializers import (
    PageMetaSerializer,
)

def get_default_data():
    return {
        "id": 0,
        "created_on": timezone.now(),
        "updated_on": timezone.now(),
        "page_url": "",
        "page_name": "Default",
        "page_title": (
            "Thrive Society - Conscious Cannabis Distribution and ",
            "Manufacturing located in Sonoma County, California"
        ),
        "meta_title": (
            "Thrive Society - Conscious Cannabis Distribution and ",
            "Manufacturing located in Sonoma County, California"
        ),
        "meta_description": (
            "Thrive Society is a collective of mission driven people, ",
            "farms and companies working together to realize the true ",
            "potential and power of the cannabis plant. We do this through ",
            "education, innovation, relationship building, technology, supply ",
            "chain empowerment and utilizing business as a force for good."
        )
    }

def normalize_url_path(url_path):
    url_path = url_path.strip()
    if not url_path.startswith('/'):
        url_path = '/' + url_path
    if not url_path.endswith('/'):
        url_path = url_path + '/'
    return url_path

# class PageMetaView(APIView):
#     """
#     Return Page Meta info from db.
#     """
#     permission_classes = (AllowAny, )

#     def get_serializer_context(self):
#         return {
#             'request': self.request,
#             'format': self.format_kwarg,
#             'view': self
#         }

#     def get(self, request, *args, **kwargs):
#         try:
#             url = request.query_params.get('url', '')
#             if not url:
#                 return Response({"detail": "Query parameter 'url' is required"}, status=400)
#             url = normalize_url_path(url)
#             try:
#                 instance = PageMeta.objects.get(page_url__iexact=url)
#             except PageMeta.DoesNotExist:
#                 return Response(get_default_data())
#         except Exception as exc:
#             return Response({"detail": exc}, status=400)
#         else:
#             serializer = PageMetaSerializer(instance, context=self.get_serializer_context)
#             return Response(serializer.data)



class PageMetaViewSet(ReadOnlyModelViewSet):
    """
    Return help docs.
    """
    queryset = PageMeta.objects.all()
    serializer_class = PageMetaSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['page_url', 'page_name', 'page_title', 'meta_title']
    permission_classes = (AllowAny,)
    pagination_class = None

    @action(
        detail=False,
        methods=['get'],
        name='Get URL Page META',
        url_name='url-page-meta',
        url_path='url-page-meta',
        # serializer_class=PageMetaSerializer,
    )
    def get_url_meta(self, request, *args, **kwargs):
        try:
            url = request.query_params.get('url', '')
            if not url:
                return Response({"detail": "Query parameter 'url' is required"}, status=400)
            url = normalize_url_path(url)
            try:
                instance = PageMeta.objects.get(page_url__iexact=url)
            except PageMeta.DoesNotExist:
                return Response(get_default_data())
        except Exception as exc:
            return Response({"detail": exc}, status=400)
        else:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
