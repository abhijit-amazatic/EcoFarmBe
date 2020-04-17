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
DEFAULT_FROM_EMAIL = "Eco-Farm <vikrant.godse@ecofarm.ag>"
DEBUG_EMAIL_RECIPIENTS = []
FRONTEND_DOMAIN_NAME = ""
#connect(host='mongodb://localhost:27017/backServA')
CELERY_BROKER_URL = 'redis://localhost:6379'
#BROKER_URL = 'redis://localhost:6379'
GOOGLE_AUTH = {
    'client_id': '<get this from heroku>',
    'client_secret': '<get this from heroku>'
}

#rest-social-auth settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile', 'https://www.googleapis.com/auth/gmail.readonly']
REST_SOCIAL_OAUTH_ABSOLUTE_REDIRECT_URI = 'https://localhost:8000/api/login/social/knox/'


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
INVENTORY_ORGANIZATION_ID=''

#Slack config
SLACK_TOKEN = ''
SLACK_CHANNEL_NAME = ''
