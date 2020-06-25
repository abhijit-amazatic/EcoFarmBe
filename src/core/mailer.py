"""
Module for send mail.
"""

from django.conf import settings
from django.core.mail import send_mail,EmailMessage
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def mail(template, context_data, subject, recipient_list, ):
    """
    Mail function to send mail.
    """
    template = get_template(template)

    content = template.render(context_data)
    msg = EmailMessage(
        subject, content, from_email="Eco-farm <%s>" % (settings.DEFAULT_FROM_EMAIL), to=[
            recipient_list]
    )
    msg.content_subtype = "html"
    msg.send()


def mail_send(template, context_data, subject, recipient_list, ):
    """
    Alternate function to send mail.
    """
    template = get_template(template)
    content = template.render(context_data)
    send_mail(subject,content,"Thrive-Society <tech@thrive-society.com>",recipient_list=[recipient_list],html_message=content)
   
