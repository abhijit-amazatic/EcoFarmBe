
"""
All periodic tasks related to brand.
"""
import datetime
from core.mailer import mail, mail_send
from django.conf import settings
from celery.task import periodic_task
from celery.schedules import crontab
from django.utils import  timezone

from integration.apps.twilio import (send_sms,)
from core.celery import app
from .models import License

@periodic_task(run_every=(crontab(hour=[1], minute=0)), options={'queue': 'general'})
def update_expired_licence_status():
    """
    Update expired licence status to 'expired'.
    """
    qs = License.objects.filter(expiration_date__lt=timezone.now())
    qs.update(status='expired')

@periodic_task(run_every=(crontab(hour=[1], minute=0)), options={'queue': 'general'})
def update_before_expire():
    """
    Update/send notification to user before expiry.(now within 2 days)  
    """
    license_obj = License.objects.filter(expiration_date__range=(timezone.now().date(),timezone.now().date()+datetime.timedelta(days=7)))
    if license_obj:
        for obj in license_obj:
            if not obj.status_before_expiry:
                obj.status_before_expiry = obj.status
                obj.save()
                print('updated license before status for ',obj.license_number)
            mail_send("license-expiry.html",{'license_number':obj.license_number,'expiration_date': obj.expiration_date.strftime('%Y-%m-%d')},"Your license will expire soon.", obj.created_by.email)   


@app.task(queue="general")
def send_async_invitation(context):
    """
    Async send organization user invitation.
    """
    context['link'] = '{}/verify-user-invitation?code={}'.format(settings.FRONTEND_DOMAIN_NAME, context['token'])

    try:
        mail_send(
            "user-invitation-mail.html",
            context,
            "Thrive Society Invitation.",
            context.get('email'),
        )
    except Exception as e:
        print(e.with_traceback)
    else:
        msg = 'You have been invited to join organization "{organizarion}" as {role}.\nPlease check your email {email}'.format(**context)
        send_sms(context['phone'], msg)