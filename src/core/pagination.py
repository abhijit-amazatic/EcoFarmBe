"""
Custom pagination for django rest framework
"""

from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination as OrignalPageNumberPagination


class PageNumberPagination(OrignalPageNumberPagination):
    """
    Wrap results with pagination data: current_page, number_of_pages, number_of_records
    """

    def get_paginated_response(self, data):
        return Response({
            'meta': {
                'current_page': self.page.number,
                'number_of_pages': self.page.paginator.num_pages,
                'number_of_records': self.page.paginator.count,
            },
            'results': data
        })
