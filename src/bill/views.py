from django.shortcuts import render
from rest_framework import (status,)
from rest_framework.permissions import (AllowAny, IsAuthenticated,)
from rest_framework.response import Response
from rest_framework.views import APIView

from bill.models import (Estimate, LineItem, )
from bill.utils import (parse_fields, get_notify_addresses, save_estimate, )
from integration.books import (create_estimate, delete_estimate, update_estimate)
from bill.tasks import (notify_estimate)
from integration.books import (send_estimate_to_sign, )

class EstimateWebappView(APIView):
    """
    View class for Web app estimates.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        """
        Get all estimates from db.
        """
        customer_name = request.query_params.get('customer_name')
        estimate_id = request.query_params.get('estimate_id')
        db_id = kwargs.get('id')
        if customer_name:
            data = Estimate.objects.filter(customer_name=customer_name)
        elif estimate_id:
            data = Estimate.objects.filter(estimate_id=estimate_id)
        elif db_id:
            data = Estimate.objects.filter(id=db_id)
        if data:
            result = dict()
            result['estimate'] = data.values()
            result['line_items'] = LineItem.objects.filter(estimate__customer_name=customer_name).values()
            return Response(result)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request):
        """
        Create and estimate in Zoho Books.
        """
        estimate_obj = save_estimate(request)
        if not estimate_obj:
            return Response({'error': 'error while creating estimate'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Success', 'id': estimate_obj.id})

    def put(self, request, **kwargs):
        """
        Update an estimate in Zoho Books.
        """
        id = kwargs.get('id', None)
        is_draft = request.query_params.get('is_draft')
        notification_methods = request.data.get('notification_methods')
        del request.data['notification_methods']
        organization_name = request.query_params.get('organization_name')
        if is_draft == 'true' or is_draft == 'True':
            estimate_obj = save_estimate(request)
            if not estimate_obj:
                return Response({'error': 'error while creating estimate'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'message': 'Updated', 'id': id})
        else:
            line_items = request.data.get('line_items')
            estimate_obj = save_estimate(request)
            estimate = Estimate.objects.get(customer_name=request.data.get('customer_name'))
            response = update_estimate(organization_name,
                                        estimate_id=estimate.estimate_id,
                                        data=request.data, params=request.query_params.dict())
            if response.get('status_code') and response['status_code'] != 0:
                response = create_estimate(organization_name, data=request.data, params=request.query_params.dict())
            response = parse_fields('estimate', response)
            if notification_methods:
                notify_addresses = get_notify_addresses(notification_methods)
            else:
                notify_addresses = list()
            sign_obj = send_estimate_to_sign(organization_name, response.get('estimate_id'),
                                             response.get('customer_name'),
                                             notify_addresses=notify_addresses)
            response['request_id'] = sign_obj.get('request_id')
            sign_url = sign_obj.get('sign_url')
            notify_estimate(notification_methods, sign_url)
            if response.get('code') and response.get('code') != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            estimate = response
            estimate['db_status'] = 'sent'
            # line_items = request.data.get('line_items')
            line_items = parse_fields('item', line_items, many=True)
            estimate_obj = Estimate.objects.filter(customer_name=estimate.get('customer_name')).update(**estimate)
            items = list()
            for item in line_items:
                item_obj = LineItem.objects.filter(estimate_id=response.get('estimate_id'), item_id=item.get('item_id')).update(**item)
            return Response(estimate)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)