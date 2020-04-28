
"""
All periodic tasks related to integrations. 
"""
from celery.task import periodic_task
from celery.schedules import crontab
from core.celery import app

from .crm import (insert_users, insert_vendors)


@app.task(queue="general")
def register_task_like_this():
    """
    This is just example to show how to register task.
    """
    pass

#@periodic_task(run_every=(crontab(minute='*')), options={'queue': 'general'})
def update_user_crm():
    """
    Update user in Zoho CRM.
    """
    #insert_users()

@periodic_task(run_every=(crontab(hour='*')), options={'queue': 'general'})
def update_vendor_crm():
    """
    Update user in Zoho CRM.
    """
    insert_vendors()