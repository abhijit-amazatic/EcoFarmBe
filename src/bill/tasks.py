from core.celery import app
from core.mailer import (mail, mail_send,)
from integration.apps.twilio import (send_sms,)
from django.conf import settings
from user.models import User
from bill.models import LineItem
from inventory.models import Inventory
from brand.models import License

@app.task(queue="urgent")
def notify_estimate(notification_methods,sign_url,customer_name,request_data, line_items):
    """
    Send estimate notifications.
    """
    print('>>>>>', request_data)
    print('====', line_items)
    order_data = list(LineItem.objects.filter(estimate__customer_name=customer_name).values())
    item_total = request_data.get('total')  #'{:,.2f}'.format(sum(i['item_total'] for i in order_data))
    quantity = sum(i['quantity'] for i in line_items)
    prod_category = Inventory.objects.filter(item_id__in=[i['item_id'] for i in  order_data],parent_category_name__isnull=False).values_list('parent_category_name',flat=True).distinct()
    category = ",".join(list(prod_category))
    license_obj = License.objects.filter(legal_business_name=customer_name).values('license_number')
    get_license_number = lambda license_obj:license_obj[0].get('license_number') if license_obj  else 0
    
    for email, notification_methods in notification_methods.items():
        try:
            full_name = User.objects.filter(email=email)[0].full_name
            if 'email' in notification_methods:
                mail_send("order-notify.html",{'sign_url': sign_url,'full_name':full_name,'order_url':settings.FRONTEND_DOMAIN_NAME+'marketplace/order','business_name': customer_name, 'license_number': get_license_number(license_obj),'order_amount':item_total,'quantity':quantity,'product_category':category},"Your Thrive-Society Order.", recipient_list=email)
            if 'sms' in notification_methods:
                context = {
                    'sign_url': sign_url,
                    'full_name':full_name,
                    'order_url':settings.FRONTEND_DOMAIN_NAME+'marketplace/order',
                    'item_total':item_total,
                    'quantity':quantity,
                    'category':category,
                    'license_number': get_license_number(license_obj),
                    'business_name':customer_name,
                    'phone': User.objects.filter(email=email).only('phone')[0].phone.as_e164
                }
                msg = 'Hi {full_name},\n\nYour Thrive Society Marketplace(Pending Order) is ready for your review & approval by accessing the following link\n: {order_url}.\nThis order is placed on behalf of {business_name}-License #{license_number}.\n\nOrder- Pending\nOrder Amount- {item_total}\nQuantity- {quantity}\nProduct Category- {category}'.format(**context)
                send_sms(context['phone'], msg)
            if 'notify' in notification_methods:
                # send_notification() To attch file to email, use mail function like this.
                #mail("order.html",{'link': settings.FRONTEND_DOMAIN_NAME+'dashboard/billing/estimates/%s/item' % estimate_id,'full_name': request.user.full_name,'order_number':order_number,'business_name': business_dba, 'license_number': document_number, 'estimate_id':estimate_id, 'order_amount':item_total,'quantity':quantity,'product_category':category},"Your Thrive Society Order %s." %order_number, request.user.email,file_data=download_pdf(request_id))
                pass
        except Exception as e:
            print('exception while sending estimate notifications',e)

    if request_data.get('external_contacts'):         
        for contact in request_data.get('external_contacts'):
            try:
                if contact.get('email'):
                    mail_send("order-notify.html",{'sign_url': sign_url,'full_name':contact.get('party_name'),'order_url':settings.FRONTEND_DOMAIN_NAME+'marketplace/order','business_name': customer_name, 'license_number': get_license_number(license_obj),'order_amount':item_total,'quantity':quantity,'product_category':category},"Your Thrive-Society Order.", recipient_list=contact.get('email'))
                if contact.get('text'):
                    context = {
                        'sign_url': sign_url,
                        'full_name':contact.get('party_name'),
                        'order_url':settings.FRONTEND_DOMAIN_NAME+'marketplace/order',
                        'item_total':item_total,
                        'quantity':quantity,
                        'category':category,
                        'license_number': get_license_number(license_obj),
                        'business_name':customer_name,
                        'phone': contact.get('text')
                    }
                    msg = 'Hi {full_name},\n\nYour Thrive Society Marketplace(Pending Order) is ready for your review & approval by accessing the following link\n: {order_url}.\nThis order is placed on behalf of {business_name}-License #{license_number}.\n\nOrder- Pending\nOrder Amount- {item_total}\nQuantity- {quantity}\nProduct Category- {category}'.format(**context)
                    send_sms(context['phone'], msg)
            except Exception as e:
                print('exception while sending notification to external contact',e)
                
            
        





