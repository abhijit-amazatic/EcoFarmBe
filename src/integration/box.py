import json
from django.core.exceptions import ObjectDoesNotExist
from .models import Integration
from boxsdk import (OAuth2, Client)
from boxsdk.exception import (BoxOAuthException,
    BoxException,)
from core.settings import (
    REDIS_URL,
    BOX_CLIENT_ID,
    BOX_CLIENT_SECRET,
    BOX_REFRESH_TOKEN,
    BOX_ACCESS_TOKEN)

def get_redis_obj():
    return redis.from_url(REDIS_URL)

def set_tokens(access_token, refresh_token):
    """
    Store box tokens in redis.
    """
    import redis
    
    db = get_redis_obj()
    redis_value = json.dumps({'access_token': access_token, 'refresh_token': refresh_token})
    db.set("box_api_tokens", redis_value)

def set_tokens_db(access_token, refresh_token):
    """
    Store box tokens in database
    """
    _, created = Integration.objects.update_or_create(
        name='box',
        defaults={
            'access_token': access_token,
            'refresh_token': refresh_token}
    )

def get_oauth2_obj():
    """
    Return Access and Refresh token.
    """
    try:
        try:
            obj = Integration.objects.get(name='box')
            access_token = obj.access_token
            refresh_token = obj.refresh_token
        except Integration.DoesNotExist:
            access_token = BOX_ACCESS_TOKEN
            refresh_token = BOX_REFRESH_TOKEN
        oauth = OAuth2(
            client_id=BOX_CLIENT_ID,
            client_secret=BOX_CLIENT_SECRET,
            access_token=access_token,
            refresh_token=refresh_token,
            store_tokens=set_tokens_db
        )
        return oauth
    except BoxOAuthException as exc:
        print(exc)
        return {'error': exc}

def get_box_tokens():
    """
    Method is used in Zoho CRM to upload file to box.
    """
    try:
        oauth2 = get_oauth2_obj()
        client = Client(oauth2)
        user = client.user().get()
        return {'status': 'success','access_token': oauth2.access_token, 'refresh_token': oauth2._refresh_token}
    except BoxException as exc:
        return {'status_code': 'error', 'error': exc}