from datetime import datetime
from integration.models import (Integration, )
from zcrmsdk.OAuthClient import ZohoOAuthTokens
from pyzoho.crm import CRM

class ZohoOAuthHandler:
    @staticmethod
    def get_oauthtokens(email_address):
        try:
            oauth_model_instance = Integration.objects.get(name='crm')
            return ZohoOAuthTokens(oauth_model_instance.refresh_token,
                                   oauth_model_instance.access_token,
                                   oauth_model_instance.expiry_time)
        except Integration.DoesNotExist:
            print('No CRM tokens in database')
            pass

    @staticmethod
    def save_oauthtokens(oauth_token):
        defaults = {
            'refresh_token': oauth_token.refreshToken,
            'access_token': oauth_token.accessToken,
            'expiry_time': oauth_token.expiryTime,
        }
        Integration.objects.update_or_create(name='crm', defaults=defaults)