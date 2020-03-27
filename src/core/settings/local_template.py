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
    '^(https?://)?127\.0\.0\.1\:9009$',
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
DEFAULT_FROM_EMAIL = "Eco-Farm <vikrant.g@amazatic.com>"
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
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile', 'https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/contacts.readonly', 'https://www.googleapis.com/auth/calendar.readonly']
REST_SOCIAL_OAUTH_ABSOLUTE_REDIRECT_URI = 'https://localhost:8000/api/login/social/knox/'

#HubSpot
HS_API_KEY = "<get this from heroku Env variable>"

#Stripe 
STRIPE_API_SECRET_KEY = "<Get this from heroku Env variable>"
STRIPE_MONTHLY_PLAN_ID = "<Get this from heroku Env variable>"
STRIPE_YEARLY_PLAN_ID = "<Get this from heroku Env variable>"
AMPLITUDE_API_KEY =  "<Get this from heroku Env variable>"
AMPLITUDE_API_SECRET =  "<Get this from heroku Env variable>"
DAU_COHORT_ID =  "<Get from Heroku Env variable>"
WAU_COHORT_ID =   "<Get from Heroku Env variable>"
