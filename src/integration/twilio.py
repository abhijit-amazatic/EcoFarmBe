"""
Twilio Integration.
"""
from core.settings import (TWILIO_ACCOUNT, TWILIO_AUTH_TOKEN,)
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from twilio.base.exceptions import TwilioRestException


def get_client():
    """
    Return twilio client.
    """
    return Client(TWILIO_ACCOUNT, TWILIO_AUTH_TOKEN)

def send_sms(to, from_, body):
    """
    Send sms to contact.
    
    @param to: receivers contact number.
    @param from: senders contact number.
    @param body: sms body.
    """
    try:
        client = get_client()
        message = client.messages.create(to=to, from_=from_, body=body)
        return message
    except TwilioRestException as exc:
        return exc

def make_call(to, from_, body,
              url='http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient'):
    """
    Make a call to contact.
    
    @param to: receivers contact number.
    @param from: senders contact number.
    @param body: sms body.
    """
    try:
        client = get_client()
        call = client.calls.create(
            to=to,
            from_=from_,
            url=url,
            twiml=get_twiml(body))
        return call
    except TwilioRestException as exc:
        return exc
    
def get_twiml(body):
    """
    Generate automated responses for twilio call.
    """
    response = VoiceResponse()
    response.say(body, loop=5)
    return response
