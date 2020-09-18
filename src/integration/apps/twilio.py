"""
Twilio Integration.
"""
from core.settings import (
    TWILIO_ACCOUNT, TWILIO_AUTH_TOKEN,
    DEFAULT_PHONE_NUMBER,)
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from twilio.base.exceptions import TwilioRestException


def get_client():
    """
    Return twilio client.
    """
    return Client(TWILIO_ACCOUNT, TWILIO_AUTH_TOKEN)

def send_sms(to, body, from_=DEFAULT_PHONE_NUMBER):
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

def make_call(to, from_, body_plain=None, body_xml=None):
    """
    Make a call to contact.
    
    @param to: receivers contact number.
    @param from: senders contact number.
    @param body_plain: plain text to send as automated voice.
    @param body_xml: already generated automated xml voice.
    """
    try:
        client = get_client()
        if body_plain:
            body_xml = get_twiml(body_plain)
        call = client.calls.create(
            to=to,
            from_=from_,
            twiml=body_xml)
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

def verification_call(to, from_=DEFAULT_PHONE_NUMBER, verification_code=None):
    """
    Call for verification with automated response.
    """
    if verification_code:
        verification_code = ' '.join(list(verification_code))
        body = f'Your verification code is {verification_code}.'
        return make_call(to=to, from_=from_, body_xml=get_twiml(body))
    return None