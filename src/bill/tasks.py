from core.celery import app

@app.task(queue="urgent")
def notify_estimate(notification_methods):
    """
    Send estimate notifications.
    """
    for email, notification_methods in notification_methods.items():
        if 'email' in notification_methods:
            # Send Email
            pass
        if 'sms' in notification_methods:
            # Send SMS
            pass
        if 'notify' in notification_methods:
            # send_notification()
            pass