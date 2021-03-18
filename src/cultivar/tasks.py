
"""
All celery tasks related to Cultivat.
"""
import datetime
import traceback
from django.conf import settings
from celery.task import periodic_task
from celery.schedules import crontab
from django.utils import  timezone
from slacker import Slacker

from core.celery import app

slack = Slacker(settings.SLACK_TOKEN)


@app.task(queue="general")
def notify_slack_cultivar_added(email, cultivar_name, cultivar_type):
    """
    as new Cultivar added, inform admin on slack.
    """
    msg = "<!channel>New Cultivar *%s* is added by user associated with the EmailID `%s`. Please review and approve the Cultivar!\n- *Cultivar Type:* %s\n" % (cultivar_name, email, cultivar_type)
    slack.chat.post_message(settings.SLACK_SALES_CHANNEL, msg, as_user=False, username=settings.BOT_NAME)

@app.task(queue="general")
def notify_slack_cultivar_Approved(email, cultivar_name, cultivar_type):
    """
    as new Cultivar approved, inform admin on slack.
    """
    msg = "<!channel>New Cultivar *%s* is approved by user associated with the EmailID `%s`.\n- *Cultivar Type:* %s\n" % (cultivar_name, email, cultivar_type)
    slack.chat.post_message(settings.SLACK_SALES_CHANNEL, msg, as_user=False, username=settings.BOT_NAME)
