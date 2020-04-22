
"""
All periodic tasks related to integrations. 
"""
from celery.task import periodic_task
from celery.schedules import crontab
from core.celery import app


@app.task(queue="general")
def register_task_like_this():
    """
    This is just example to show how to register task.
    """
    pass


@periodic_task(run_every=(crontab(hour=[1], minute=1)), options={'queue': 'general'})
def periodic_task_example():
    """
    This is just example to show how run periodic tasks.
    """
    pass
