# pylint:disable = all
# SECURITY WARNING: keep the secret key used in production secret!
#import djcelery
from mongoengine import connect
SECRET_KEY = ''
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
PRODUCTION = False
DATABASES = {
    'default': {
        'ENGINE': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': ''
    },
    'logger': {
        'ENGINE': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': ''
    },
}
DATABASE_ROUTERS = [
    'core.db_routers.LoggerRouter',
    # 'core.db_routers.defaultRouter',
]

REDIS_URL = ''

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
#SENDGRID_API_KEY = ""

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
import os
cwd = os.getcwd()

# Zoho Default configuration
ZOHO_CLIENT_ID = ''
ZOHO_CLIENT_SECRET = ''
ZOHO_REDIRECT_URI = ''


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
    # 'token_persistence_path':'',
    # 'access_type':'offline',
    'persistence_handler_class' : 'ZohoOAuthHandler',
    'persistence_handler_path': cwd + '/src/core/persist_crm_token.py'
}

if DEBUG:
    PYZOHO_CONFIG['sandbox'] = 'true'
    PYZOHO_CONFIG['client_id'] = ''
    PYZOHO_CONFIG['client_secret'] = ''
    PYZOHO_REFRESH_TOKEN=''
    PYZOHO_USER_IDENTIFIER=''

PYZOHO_SCOPE = 'ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL,ZohoCRM.org.ALL,ZohoCRM.coql.READ'


#Zoho Inventory configuration
INVENTORY_CLIENT_ID=''
INVENTORY_CLIENT_SECRET=''
INVENTORY_REDIRECT_URI=''
INVENTORY_SCOPE = 'ZohoInventory.fullaccess.all'
INVENTORY_REFRESH_TOKEN=''
INVENTORY_ORGANIZATION_ID = ''
INVENTORY_EFD_ORGANIZATION_ID=''
INVENTORY_EFL_ORGANIZATION_ID=''
INVENTORY_EFN_ORGANIZATION_ID = ''
INVENTORY_TAXES = ''
INVENTORY_BOX_ID='118042804025'

#Zoho Books configuration
BOOKS_CLIENT_ID=''
BOOKS_CLIENT_SECRET=''
BOOKS_REDIRECT_URI=''
BOOKS_SCOPE = 'ZohoBooks.fullaccess.all'
BOOKS_REFRESH_TOKEN=''
BOOKS_ORGANIZATION_ID=''
BOOKS_ORGANIZATION_EFD_ID=''
BOOKS_ORGANIZATION_EFL_ID=''
BOOKS_ORGANIZATION_EFN_ID=''
ESTIMATE_TAXES = {'Flower': 'Cultivation Tax - Flower (2020)', 'Trim': 'Cultivation Tax - Trim (2020)'}
TRANSPORTATION_FEES = 'Transportation Fees'
#BOOKS_ORGANIZATION_LIST = ['books_efd', 'books_efl', 'books_efn']
BOOKS_ORGANIZATION_LIST = "books_efd,books_efl,books_efn"

#Zoho Sign configuration
SIGN_CLIENT_ID=''
SIGN_CLIENT_SECRET=''
SIGN_REDIRECT_URI=''
SIGN_SCOPE = 'ZohoSign.documents.ALL,ZohoSign.templates.ALL'
SIGN_REFRESH_TOKEN=''
SIGN_HOST_URL = ''
ESTIMATE_UPLOAD_FOLDER_ID=''
FARM_FOLDER_ID = ''

#Zoho Campaign configs
CAMPAIGN_CLIENT_ID=''
CAMPAIGN_CLIENT_SECRET=''
CAMPAIGN_REDIRECT_URI=''
CAMPAIGN_SCOPE = 'ZohoCampaigns.campaign.ALL,ZohoCampaigns.contact.ALL'
CAMPAIGN_REFRESH_TOKEN=''
CAMPAIGN_HTML_BUCKET=''

#Box configuration get those tokens from heroku or team mate.
BOX_CLIENT_ID=''
BOX_CLIENT_SECRET=''
BOX_REFRESH_TOKEN=''
BOX_ACCESS_TOKEN=''
LICENSE_PARENT_FOLDER_ID='113146023153'
TEMP_LICENSE_FOLDER='111282192684'
BOX_JWT_DICT = {}
BOX_JWT_USER = ''


#Slack config
SLACK_TOKEN = ''
SLACK_CHANNEL_NAME = 'tech_dev_slack_testing' #PROD: 'tech_new_website_users'
#sales channel
SLACK_SALES_CHANNEL = 'tech_dev_slack_testing' #PROD:'sales_leads'
#profile channel
SLACK_PROFILE_CHANNEL = 'tech_dev_slack_testing' #PROD: 'tech_new_website_onboarding_profiles'
#inventory channel
SLACK_INVENTORY_CHANNEL = 'tech_dev_slack_testing' #PROD: 'distro_new_inventory_items_web_app'
#inventory item edit channel
SLACK_ITEM_EDIT_CHANNEL = 'tech_dev_slack_testing' #PROD: 'distro_inventory_item_edit_web_app'
#inventory item delist channel
SLACK_ITEM_DELIST_CHANNEL = 'tech_dev_slack_testing' #PROD: 'distro_inventory_item_delist_web_app'
#Logistics Transport channel
SLACK_LOGISTICS_TRANSPORT_CHANNEL = 'tech_dev_slack_testing' #PROD: 'distro_logistics_transport_requests_web_app'

#NEW CULTIVARS
SLACK_NEW_CULTIVARS = 'tech_dev_slack_testing'
#eco farm bot
BOT_NAME= 'Thrive-Society-Bot'
BOT_ICON_URL= 'https://www.thrive-society.com/static/media/logo.f8a96e86.png'

#Admin email
ADMIN_EMAIL = 'tech@ecofarm.ag'
#Inventory Notification Email
NOTIFICATION_EMAIL_INVENTORY = 'tech@ecofarm.ag'
#Logistics Transport Notification Email
NOTIFICATION_EMAIL_LOGISTICS_TRANSPORT = 'tech@ecofarm.ag' #PROD: logistics@thrive-society.com 

#layouts
VENDOR_LAYOUT = {
    "vendor_cannabis": "4230236000001999777",
    "vendor_cannabis_non_cultivator": "4230236000002263267",
    "vendor_cannabis_nursery": "4230236000004898031"
}
LEADS_LAYOUT = {
    "accounts": "4230236000001156737",
    "vendor_cannabis_cultivar": "4230236000001229441",
    "vendor_cannabis_non_cultivator": "4230236000001229442",
    "vendor_non_cannabis": "4230236000001229443",
    }
LICENSE_LAYOUT = {
    "cultivar": "4230236000002267946",
    "non-cultivar": "4230236000002267947"
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

AUTHY_USER_REGISTRATION_CALLBACK_SIGNING_KEY=''
BCC_APP_ID = ''
BCC_APP_KEY = ''

ZOHO_CRM_URL = ''
CRM_ORGANIZATION_ID = ''

#AWS for ckeditor(keynames are different than above used aws)
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_STORAGE_BUCKET_NAME = 'help-documentation'

NUMBER_OF_DAYS_TO_FETCH_INVENTORY=150

ONBOARDING_DATA_FETCH_EMAIL_OVERRIDE = []

BACKEND_DOMAIN_NAME = 'eco-farm-staging.herokuapp.com'

CUSTOM_INVENTORY_WAREHOUSE_NAME = 'Test Books Organization'

INVENTORY_CSV_UPLOAD_FOLDER_ID = '133586884521'

INVENTORY_QR_UPLOAD_FOLDER_ID = '149397343347'

IS_SANDBOX = True
ENV_PREFIX ='' #'dev-' for stag & 'prod-' for prod

#pendo config
TRACK_EVENT_SECRET_KEY = ''

#Notifications
ONBOARDING_ADMIN_EMAIL = '' #
SLACK_ONBOARDING_PROGRESS = ''
SLACK_ONBOARDING_COMPLETED = {}

PRODUCTION = 'false'
INTERNAL_USER_DEFAULT_ORG_ID = ''
#bypass email & phone verification for listed signed up email
BYPASS_VERIFICATION_FOR_EMAILS = []


# DRF API Logger
DRF_API_LOGGER_DATABASE = True
DRF_API_LOGGER_EXCLUDE_KEYS = ['password', 'token', 'access', 'refresh', 'Token']
DRF_API_LOGGER_DEFAULT_DATABASE = 'logger'
DRF_API_LOGGER_SKIP_URL_NAME = [
    'page-meta-list',
    'page-meta-detail',
    'page-meta-url-page-meta',
]

INTEGRATION_ADMIN_EMAILS = []
INTEGRATION_ADMIN_TOKEN_MASK = True


PASSWORDLESS_AUTH = {
    'PASSWORDLESS_AUTH_TYPES': ['EMAIL', 'PHONE'],
    'PASSWORDLESS_REGISTER_NEW_USERS': False,
    'PASSWORDLESS_USER_MOBILE_FIELD_NAME':'phone',
    'PASSWORDLESS_EMAIL_NOREPLY_ADDRESS': "Thrive Society <support@thrive-society.com>",
    # 'PASSWORDLESS_MOBILE_MESSAGE':"Do not share this OTP with anyone.Use this code to log in with Thrive Society: %s",
    'PASSWORDLESS_MOBILE_MESSAGE':"Your verification code is %s",
    'PASSWORDLESS_EMAIL_TOKEN_HTML_TEMPLATE_NAME': "passwordless.html",
    'PASSWORDLESS_MOBILE_NOREPLY_NUMBER': '+18558055506',
    'TWILIO_ACCOUNT_SID':'',
    'TWILIO_AUTH_TOKEN':''       
}


AWS_OUTPUT_BUCKET='compressed-ecofarm-staging'
INVENTORY_IMAGE_CROP_RATIO=1.6

#Confia
CONFIA_ACCESS_KEY = ''
CONFIA_ACCESS_SECRET = ''
CONFIA_BASIC_CALLBACK_USER_PW = ""
CONFIA_ACCESS_ID = ''
CONFIA_API_BASE_URL= 'https://sandbox.pointchain.io/partner/'

#Rapid API
RAPID_API_KEY = ''

#Box Sign
BOX_SIGN_W9_TEMPLATE_ID = ''
