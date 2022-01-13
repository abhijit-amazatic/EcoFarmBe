"""
All periodic tasks related to brand.
"""
import datetime
from re import search
import traceback
from core.mailer import mail, mail_send
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from celery.task import periodic_task
from celery.schedules import crontab
from django.utils import timezone
from slacker import Slacker

from integration.apps.twilio import (
    send_sms,
)
from integration.crm import (
    insert_records,
)
from core.celery import app
from core.utility import (
    notify_admins_on_profile_user_registration,
)
from ..models import (
    License,
)

from .license_oboarding_tasks import (
    send_license_onboarding_verification_task,
    resend_license_onboarding_verification_task,
    onboarding_verified_license_data_population_task,
)
from .license_user_invite_tasks import (
    invite_license_user_task,
    invite_profile_contacts_task,
)
from .create_customer_in_books import (
    create_customer_in_books_task,
)

from .refresh_integration_ids import (
    refresh_integration_ids_task,
)
slack = Slacker(settings.SLACK_TOKEN)


@periodic_task(run_every=(crontab(hour=[1], minute=0)), options={"queue": "general"})
def update_expired_license_status():
    """
    Update expired licence status to 'Expired'.
    """
    qs = License.objects.filter(expiration_date__lt=timezone.now())
    qs.update(license_status="Expired")


@periodic_task(run_every=(crontab(hour=[1], minute=0)), options={"queue": "general"})
def update_before_expire():
    """
    Update/send notification to user before expiry.(now within 2 days)
    """
    license_obj = License.objects.filter(
        expiration_date__range=(
            timezone.now().date(),
            timezone.now().date() + datetime.timedelta(days=7),
        )
    )
    if license_obj:
        for obj in license_obj:
            # if not obj.status_before_expiry:
            #     obj.status_before_expiry = obj.status
            #     obj.save()
            #     print("updated license before status for ", obj.license_number)
            if not obj.is_notified_before_expiry:
                mail_send(
                    "license-expiry.html",
                    {
                        "license_number": obj.license_number,
                        "expiration_date": obj.expiration_date.strftime("%Y-%m-%d"),
                    },
                    "Your license will expire soon.",
                    obj.created_by.email,
                )
                obj.is_notified_before_expiry = True
                obj.save()
                print(
                    "Notified License before expiry & flagged as notified",
                    obj.license_number,
                )


@app.task(queue="general")
def insert_record_to_crm(license_id, is_update=False, account_crm_id=None, vendor_crm_id=None):
    """
    Insert record to crm and create/update customer and vendor to books.
    """
    r = insert_records(
        id=license_id,
        is_update=is_update,
        account_crm_id=account_crm_id,
        vendor_crm_id=vendor_crm_id,
    )
    create_customer_in_books_task.delay(license_id)
    return r
