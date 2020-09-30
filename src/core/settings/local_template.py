# pylint:disable = all
# SECURITY WARNING: keep the secret key used in production secret!
#import djcelery
from mongoengine import connect
SECRET_KEY = ''
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': ''
    }
}
ALLOWED_HOSTS = []

CORS_ORIGIN_REGEX_WHITELIST = (
    '^(https?://)?127\.0\.0\.1\:8000$',
    '^https\:\/\/127\.0\.0\.1\:9009$',
    '^https?\:\/\/example\-dashboard\.herokuapp\.com$',
)

# python -m smtpd -n -c DebuggingServer localhost:1025
# or email_backend 'django.core.mail.backends.console.EmailBackend'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = "Eco-Farm <tech@ecofarm.ag>"
DEBUG_EMAIL_RECIPIENTS = []
SENDGRID_API_KEY = ""

FRONTEND_DOMAIN_NAME = ""
#connect(host='mongodb://localhost:27017/backServA')
CELERY_BROKER_URL = 'redis://localhost:6379'
#BROKER_URL = 'redis://localhost:6379'
GOOGLE_AUTH = {
    'client_id': '<get this from heroku>',
    'client_secret': '<get this from heroku>'
}

#rest-social-auth settings
# SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
# SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''
# SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile', 'https://www.googleapis.com/auth/gmail.readonly']
# REST_SOCIAL_OAUTH_ABSOLUTE_REDIRECT_URI = 'https://localhost:8000/api/login/social/knox/'

#For persistence handler class.
#import os
#cwd = os.getcwd()

#Zoho Take credential from the team.
PYZOHO_CONFIG = {
'apiBaseUrl':'https://www.zohoapis.com',
'apiVersion':'v2',
'currentUserEmail':'',
'sandbox':'false',
'applicationLogFilePath':'',
'client_id':'',
'client_secret':'',
'redirect_uri':'',
'accounts_url':'',
'token_persistence_path':'',
'access_type':'offline',
#'persistence_handler_class' : 'ZohoOAuthHandler',
#'persistence_handler_path': cwd + '/src/core/persist_crm_token.py'
}

if DEBUG:
    PYZOHO_CONFIG['sandbox'] = 'true'
    PYZOHO_CONFIG['client_id'] = ''
    PYZOHO_CONFIG['client_secret'] = ''
    PYZOHO_REFRESH_TOKEN=''
    PYZOHO_USER_IDENTIFIER=''


REDIS_URL = ''
#Box configuration get those tokens from heroku or team mate.
BOX_CLIENT_ID=''
BOX_CLIENT_SECRET=''
BOX_REFRESH_TOKEN=''
BOX_ACCESS_TOKEN=''    

#Zoho Inventory configuration
INVENTORY_CLIENT_ID=''
INVENTORY_CLIENT_SECRET=''
INVENTORY_REFRESH_TOKEN=''
INVENTORY_REDIRECT_URI=''
INVENTORY_EFD_ORGANIZATION_ID=''
INVENTORY_EFL_ORGANIZATION_ID=''
INVENTORY_TAXES = ''
INVENTORY_BOX_ID='118042804025'

#Zoho Books configuration
BOOKS_CLIENT_ID=''
BOOKS_CLIENT_SECRET=''
BOOKS_ORGANIZATION_ID=''
BOOKS_REDIRECT_URI=''
BOOKS_REFRESH_TOKEN=''
ESTIMATE_TAXES = {'Flower': 'Cultivation Tax - Flower (2020)', 'Trim': 'Cultivation Tax - Trim (2020)'}
TRANSPORTATION_FEES = 'Transportation Fees'
LICENSE_PARENT_FOLDER_ID='113146023153'

#Zoho Sign configuration
SIGN_CLIENT_ID=''
SIGN_CLIENT_SECRET=''
SIGN_REDIRECT_URI=''
SIGN_REFRESH_TOKEN=''
SIGN_HOST_URL = ''
ESTIMATE_UPLOAD_FOLDER_ID=''
FARM_FOLDER_ID = ''

#Slack config
SLACK_TOKEN = ''
SLACK_CHANNEL_NAME = '' #tech_new_website_users #tech_dev_slack_testing

#Admin email
ADMIN_EMAIL = 'tech@ecofarm.ag'

#layouts
VENDOR_LAYOUT = "4230236000001156761"

LEADS_LAYOUT = {
    "accounts": "4230236000001156737",
    "vendor_cannabis_cultivar": "4230236000001229441",
    "vendor_cannabis_non_cultivator": "4230236000001229442",
    "vendor_non_cannabis": "4230236000001229443",
    }

GOOGLEMAPS_API_KEY=''
TWILIO_ACCOUNT=''
TWILIO_AUTH_TOKEN=''
DEFAULT_PHONE_NUMBER=''

TMP_DIR = ''

#AWS creds
AWS_CLIENT_ID=''
AWS_CLIENT_SECRET = ''
AWS_BUCKET = ''
AWS_REGION = ''

# Authy Application Key
# You can get/create one here: https://www.twilio.com/console/authy/applications
AUTHY_ACCOUNT_SECURITY_API_KEY=''
AUTHY_APP_ID=''
AUTHY_APP_NAME=''
