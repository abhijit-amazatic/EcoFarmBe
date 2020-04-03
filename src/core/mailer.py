"""
Module for send mail.
"""

from django.conf import settings

from django.core.mail import EmailMessage
from django.template.loader import get_template


def mail(template, context_data, subject, recipient_list, ):
    """
    Mail function to send mail.
    """
    template = get_template(template)

    content = template.render(context_data)
    msg = EmailMessage(
        subject, content, from_email="Fabriq <%s>" % (settings.DEFAULT_FROM_EMAIL), to=[
            recipient_list]
    )
    msg.content_subtype = "html"
    msg.send()
