from core.celery import app
from core.mailer import (mail, mail_send,)
from integration.apps.twilio import (send_sms,)
from user.models import User

@app.task(queue="urgent")
def notify_estimate(notification_methods,sign_url):
    """
    Send estimate notifications.
    """
    for email, notification_methods in notification_methods.items():
        try:
            if 'email' in notification_methods:
                mail_send("order-notify.html",{'sign_url': sign_url},"Thrive-Society Order Sign Link.", recipient_list=email)
            if 'sms' in notification_methods:
                context = {
                    'sign_url': sign_url,
                    'phone': User.objects.filter(email=email).only('phone')[0].phone.as_e164
                }
                msg = 'Your Thrive Society Marketplace(Pending Order) is ready for review & sign.\nSignature link is {sign_url}'.format(**context)
                send_sms(context['phone'], msg)
            if 'notify' in notification_methods:
                # send_notification() To attch file to email, use mail function like this.
                #mail("order.html",{'link': settings.FRONTEND_DOMAIN_NAME+'dashboard/billing/estimates/%s/item' % estimate_id,'full_name': request.user.full_name,'order_number':order_number,'business_name': business_dba, 'license_number': document_number, 'estimate_id':estimate_id, 'order_amount':item_total,'quantity':quantity,'product_category':category},"Your Thrive Society Order %s." %order_number, request.user.email,file_data=download_pdf(request_id))
                pass
        except Exception as e:
            print('exception while sending estimate notifications',e)
            






