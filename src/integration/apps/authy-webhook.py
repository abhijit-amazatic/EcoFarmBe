import base64
import hashlib
import hmac
import json
import os
import pprint
import requests
import re
from datetime import datetime
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

from config import (
    APP_API_KEY,
    ACCESS_KEY,
    API_SIGNING_KEY,
)

pp = pprint.PrettyPrinter(indent=4, compact=False)

class WebhookApi:
    url = 'https://api.authy.com/dashboard/json/application/webhooks'
    app_api_key=''
    access_key=''
    api_signing_key=''

    def __init__(self, app_api_key, access_key, api_signing_key):
        self.app_api_key=app_api_key
        self.access_key=access_key
        self.api_signing_key=api_signing_key

    def create(self, name, callback_url, events):
        """
        list hooks
        """
        data = {
            'url': callback_url,
            'events': events,
            'name': name,
            'app_api_key': self.app_api_key,
            'access_key': self.access_key,
        }
        nonce = str(datetime.utcnow().timestamp())
        headers = {
            'X-Authy-Signature-Nonce': nonce,
            'X-Authy-Signature': self.calculate_signature(self.url, nonce, 'POST', data),

        }
        response = requests.post(self.url, data=data, headers=headers)
        print('Status code: ', response.status_code)
        pp.pprint(response.json())
        print()
        return response.json()

    def delete(self, webhook_id):
        """
        list hooks
        """
        data = {
            'app_api_key': self.app_api_key,
            'access_key': self.access_key,
        }
        nonce = str(datetime.utcnow().timestamp())
        url = self.url + '/' + webhook_id
        headers = {
            'X-Authy-Signature-Nonce': nonce,
            'X-Authy-Signature': self.calculate_signature(url, nonce, 'DELETE', data),

        }
        response = requests.delete(url, data=data, headers=headers)
        print('Status code: ', response.status_code)
        pp.pprint(response.json())
        print()
        return response.json()

    def list(self):
        """
        list hooks
        """
        data = {
            'app_api_key': self.app_api_key,
            'access_key': self.access_key,
        }
        nonce = str(datetime.utcnow().timestamp())
        headers = {
            'X-Authy-Signature-Nonce': nonce,
            'X-Authy-Signature': self.calculate_signature(self.url, nonce, 'GET', data),

        }
        response = requests.get(self.url, data=data, headers=headers)
        print('Status code: ', response.status_code)
        pp.pprint(response.json())
        print()
        return response.json()

    def calculate_signature(self, url, nonce, method, params):
        """
        Function to validate signature in X-Authy-Signature key of headers.

        :param string signature: X-Authy-Signature key of headers.
        :param string nonce: X-Authy-Signature-Nonce key of headers.
        :param string method: GET or POST - configured in app settings for OneTouch.
        :param string url: base callback url.
        :param dict params: params sent by Authy.
        :return bool: True if calculated signature and X-Authy-Signature are identical else False.
        """
        query_params = self.__make_http_query(params)
        # Sort and replace encoded  params in case-sensitive order
        sorted_params = '&'.join(sorted(query_params.replace(
            '/', '%2F').replace('%20', '+').split('&')))
        sorted_params = re.sub("\\%5B([0-9])*\\%5D", "%5B%5D", sorted_params)
        sorted_params = re.sub("\\=None", "=", sorted_params)
        data = nonce + "|" + method + "|" + url + "|" + sorted_params
        try:
            calculated_signature = base64.b64encode(
                hmac.new(self.api_signing_key.encode(), data.encode(), hashlib.sha256).digest())
            return calculated_signature.decode()
        except:
            calculated_signature = base64.b64encode(
                hmac.new(self.api_signing_key, data, hashlib.sha256).digest())
            return calculated_signature

    def __make_http_query(self, params, topkey=''):
        """
        Function to covert params into url encoded query string
        :param dict params: Json string sent  by Authy.
        :param string topkey: params key
        :return string: url encoded Query.
        """
        if len(params) == 0:
            return ""
        result = ""
        # is a dictionary?
        if type(params) is dict:
            for key in params.keys():
                newkey = quote(key)
                if topkey != '':
                    newkey = topkey + quote('[' + key + ']')
                if type(params[key]) is dict:
                    result += self.__make_http_query(params[key], newkey)
                elif type(params[key]) is list:
                    i = 0
                    for val in params[key]:
                        if type(val) is dict:
                            result += self.__make_http_query(
                                val, newkey + quote('['+str(i)+']'))
                        else:
                            result += newkey + \
                                quote('['+str(i)+']') + "=" + \
                                quote(str(val)) + "&"
                        i = i + 1
                # boolean should have special treatment as well
                elif type(params[key]) is bool:
                    result += newkey + "=" + \
                        quote(str(params[key]).lower()) + "&"
                # assume string (integers and floats work well)
                else:
                    result += newkey + "=" + quote(str(params[key])) + "&"
        # remove the last '&'
        if (result) and (topkey == '') and (result[-1] == '&'):
            result = result[:-1]
        return result


webhook_api = WebhookApi(app_api_key=APP_API_KEY, access_key=ACCESS_KEY, api_signing_key=API_SIGNING_KEY)

if __name__ == "__main__":
    # webhook_api.create('test_user_regi', 'https://3e5b257cf31f.ngrok.io/two-factor/authy-callback/user-registration/', 'user_registration_completed',)
    # webhook_api.delete('WH_6a554f7f-4433-4a25-ba5d-0f083733c790')
    webhook_api.list()
