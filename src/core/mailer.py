"""
Module for send mail.
"""

from django.conf import settings
from django.core.mail import send_mail,EmailMessage
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def mail(template, context_data, subject, recipient_list, file_data=None,):
    """
    Mail function to send mail.
    """
    template = get_template(template)

    content = template.render(context_data)
    msg = EmailMessage(
        subject, content, from_email="Thrive Society <support@thrive-society.com>", to=[
            recipient_list]
    )
    msg.content_subtype = "html"
    if file_data:
        #msg.attach_file(file_path)
        msg.attach("Order.pdf", file_data, "application/pdf")
    msg.send()


def mail_send(template, context_data, subject, recipient_list, ):
    """
    Alternate function to send mail.
    """
    template = get_template(template)
    content = template.render(context_data)
    send_mail(subject,content,"Thrive Society <support@thrive-society.com>",recipient_list=[recipient_list],html_message=content)
   
