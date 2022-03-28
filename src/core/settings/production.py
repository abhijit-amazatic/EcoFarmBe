import os
import json
import dj_database_url

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'true').lower() == "true"
PRODUCTION = os.environ.get('PRODUCTION', 'false').lower() == "true"
DEFAULT_CONNECTION = dj_database_url.parse(os.environ.get("DATABASE_URL"))
DEFAULT_CONNECTION.update({"CONN_MAX_AGE": 600})
LOGGER_CONNECTION = dj_database_url.parse(os.environ.get("LOGGER_DATABASE_URL"))
LOGGER_CONNECTION.update({"CONN_MAX_AGE": 600})
DATABASES = {
    "default": DEFAULT_CONNECTION,
    'logger': LOGGER_CONNECTION,

}
DATABASE_ROUTERS = [
    'core.db_routers.LoggerRouter',
    # 'core.db_routers.defaultRouter',
]
REDIS_URL = os.environ.get('REDIS_URL')

ALLOWED_HOSTS = json.loads(os.environ.get("ALLOWED_HOSTS", "[\"*\"]"))
CORS_ORIGIN_REGEX_WHITELIST = json.loads(os.environ.get("CORS_ORIGIN", "[]"))
FRONTEND_DOMAIN_NAME = os.environ.get("FRONTEND_DOMAIN_NAME")

# Must generate specific password for your app in [gmail settings][1]
#SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
EMAIL_HOST = 'smtp.mailgun.org'  # 'smtp.sendgrid.net'
EMAIL_HOST_USER = os.getenv("MAILGUN_SMTP_LOGIN") #'apikey'
EMAIL_HOST_PASSWORD = os.getenv("MAILGUN_SMTP_PASSWORD") #'SENDGRID_API_KEY'
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_USE_TLS = True

# Celery settings.
CELERY_BROKER_URL = os.environ.get('CLOUDAMQP_URL')
CELERY_BROKER_POOL_LIMIT = int(os.environ.get('CELERY_BROKER_POOL_LIMIT'))
#CELERY_RESULT_BACKEND = os.environ.get("CLOUDAMQP_URL")

# Google Credentials.
# GOOGLE_AUTH = {
#    'client_id': os.getenv('GOOGLE_CLIENT_ID'),
#    'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
# }

# social-rest-knox settings.
#SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_CLIENT_ID'),
#SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_CLIENT_SECRET'),
#SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile', 'https://www.googleapis.com/auth/gmail.readonly']
#REST_SOCIAL_OAUTH_ABSOLUTE_REDIRECT_URI  = os.getenv('REST_SOCIAL_OAUTH_ABSOLUTE_REDIRECT_URI')

# For persistence handler class
# cwd = os.getcwd()

# Integration Admin
INTEGRATION_ADMIN_EMAILS = json.loads(os.environ.get("INTEGRATION_ADMIN_EMAILS", "[]"))
INTEGRATION_ADMIN_TOKEN_MASK = os.environ.get('INTEGRATION_ADMIN_TOKEN_MASK', 'true').lower() != 'false'

# Zoho Default configuration
ZOHO_CLIENT_ID = os.environ.get('ZOHO_CLIENT_ID')
ZOHO_CLIENT_SECRET = os.environ.get('ZOHO_CLIENT_SECRET')
ZOHO_REDIRECT_URI = os.environ.get('ZOHO_REDIRECT_URI')

PYZOHO_CONFIG = {
    'apiBaseUrl': 'https://www.zohoapis.com',
    'apiVersion': 'v2',
    'currentUserEmail': os.environ.get('PYZOHO_USER'),
    'sandbox': os.environ.get('IS_SANDBOX'),
    'applicationLogFilePath': '',
    'client_id': os.environ.get('PYZOHO_CLIENT_ID', ZOHO_CLIENT_ID),
    'client_secret': os.environ.get('PYZOHO_CLIENT_SECRET', ZOHO_CLIENT_SECRET),
    'redirect_uri': os.environ.get('PYZOHO_REDIRECT_URL', ZOHO_REDIRECT_URI),
    'accounts_url': os.environ.get('PYZOHO_ACCOUNT_URL'),
    # 'token_persistence_path': os.environ.get('TOKEN_PERSISTENCE_PATH'),
    # 'access_type': 'offline',
    'persistence_handler_class' : 'ZohoOAuthHandler',
    'persistence_handler_path': '/app/src/core/persist_crm_token.py'
}
# if DEBUG:
#     PYZOHO_CONFIG['sandbox'] = 'true'

PYZOHO_SCOPE = os.environ.get(
    'PYZOHO_SCOPE',
    'ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL,ZohoCRM.org.ALL,ZohoCRM.coql.READ',
)
PYZOHO_REFRESH_TOKEN = os.environ.get('PYZOHO_REFRESH_TOKEN')
PYZOHO_USER_IDENTIFIER = os.environ.get('PYZOHO_USER')

# Zoho Inventory configuration
INVENTORY_CLIENT_ID = os.environ.get('INVENTORY_CLIENT_ID', ZOHO_CLIENT_ID)
INVENTORY_CLIENT_SECRET = os.environ.get('INVENTORY_CLIENT_SECRET', ZOHO_CLIENT_SECRET)
INVENTORY_REDIRECT_URI = os.environ.get('INVENTORY_REDIRECT_URI', ZOHO_REDIRECT_URI)
INVENTORY_SCOPE = os.environ.get('INVENTORY_SCOPE', 'ZohoInventory.fullaccess.all')
INVENTORY_REFRESH_TOKEN = os.environ.get('INVENTORY_REFRESH_TOKEN')
INVENTORY_ORGANIZATION_ID = os.environ.get('INVENTORY_ORGANIZATION_ID')
INVENTORY_EFD_ORGANIZATION_ID = os.environ.get('INVENTORY_EFD_ORGANIZATION_ID')
INVENTORY_EFL_ORGANIZATION_ID = os.environ.get('INVENTORY_EFL_ORGANIZATION_ID')
INVENTORY_EFN_ORGANIZATION_ID = os.environ.get('INVENTORY_EFN_ORGANIZATION_ID')
INVENTORY_TAXES = os.environ.get('INVENTORY_TAXES')
INVENTORY_BOX_ID = os.environ.get('INVENTORY_BOX_ID')

# Zoho Books configuration
BOOKS_CLIENT_ID = os.environ.get('BOOKS_CLIENT_ID', ZOHO_CLIENT_ID)
BOOKS_CLIENT_SECRET = os.environ.get('BOOKS_CLIENT_SECRET', ZOHO_CLIENT_SECRET)
BOOKS_REDIRECT_URI = os.environ.get('BOOKS_REDIRECT_URI', ZOHO_REDIRECT_URI)
BOOKS_SCOPE = os.environ.get('BOOKS_SCOPE', 'ZohoBooks.fullaccess.all')
BOOKS_REFRESH_TOKEN = os.environ.get('BOOKS_REFRESH_TOKEN')
BOOKS_ORGANIZATION_ID = os.environ.get('BOOKS_ORGANIZATION_ID')
BOOKS_ORGANIZATION_EFD_ID = os.environ.get('BOOKS_ORGANIZATION_EFD_ID'),
BOOKS_ORGANIZATION_EFL_ID = os.environ.get('BOOKS_ORGANIZATION_EFL_ID'),
BOOKS_ORGANIZATION_EFN_ID = os.environ.get('BOOKS_ORGANIZATION_EFN_ID'),
ESTIMATE_TAXES = os.environ.get('ESTIMATE_TAXES')
BOOKS_ORGANIZATION_LIST = os.environ.get('BOOKS_ORGANIZATION_LIST')

# Zoho Sign configuration
SIGN_CLIENT_ID = os.environ.get('SIGN_CLIENT_ID', ZOHO_CLIENT_ID)
SIGN_CLIENT_SECRET = os.environ.get('SIGN_CLIENT_SECRET', ZOHO_CLIENT_SECRET)
SIGN_REDIRECT_URI = os.environ.get('SIGN_REDIRECT_URI', ZOHO_REDIRECT_URI)
SIGN_SCOPE = os.environ.get('SIGN_SCOPE', 'ZohoSign.documents.ALL,ZohoSign.templates.ALL')
SIGN_REFRESH_TOKEN = os.environ.get('SIGN_REFRESH_TOKEN')
SIGN_HOST_URL = os.environ.get('SIGN_HOST_URL')
ESTIMATE_UPLOAD_FOLDER_ID = os.environ.get('ESTIMATE_UPLOAD_FOLDER_ID')
TRANSPORTATION_FEES = os.environ.get('TRANSPORTATION_FEES')
FARM_FOLDER_ID = os.environ.get('FARM_FOLDER_ID')

#Zoho Campaign configs
CAMPAIGN_CLIENT_ID = os.environ.get('CAMPAIGN_CLIENT_ID', ZOHO_CLIENT_ID)
CAMPAIGN_CLIENT_SECRET = os.environ.get('CAMPAIGN_CLIENT_SECRET', ZOHO_CLIENT_SECRET)
CAMPAIGN_REDIRECT_URI = os.environ.get('CAMPAIGN_REDIRECT_URI', ZOHO_REDIRECT_URI)
CAMPAIGN_SCOPE = os.environ.get('CAMPAIGN_SCOPE', 'ZohoCampaigns.campaign.ALL,ZohoCampaigns.contact.ALL')
CAMPAIGN_REFRESH_TOKEN = os.environ.get('CAMPAIGN_REFRESH_TOKEN')
CAMPAIGN_HTML_BUCKET = os.environ.get('CAMPAIGN_HTML_BUCKET')

# Box configuration
BOX_CLIENT_ID = os.environ.get('BOX_CLIENT_ID')
BOX_CLIENT_SECRET = os.environ.get('BOX_CLIENT_SECRET')
BOX_REFRESH_TOKEN = os.environ.get('BOX_REFRESH_TOKEN')
BOX_ACCESS_TOKEN = os.environ.get('BOX_ACCESS_TOKEN')
LICENSE_PARENT_FOLDER_ID = os.environ.get('LICENSE_PARENT_FOLDER_ID')
TEMP_LICENSE_FOLDER = os.environ.get('TEMP_LICENSE_FOLDER')
BOX_JWT_DICT = os.environ.get('BOX_JWT_DICT')
BOX_JWT_USER = os.environ.get('BOX_JWT_USER')

# slack tokens'
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_CHANNEL_NAME = os.environ.get("SLACK_CHANNEL_NAME")
#sales
SLACK_SALES_CHANNEL = os.environ.get("SLACK_SALES_CHANNEL")
#PROFILE
SLACK_PROFILE_CHANNEL = os.environ.get("SLACK_PROFILE_CHANNEL")
#Inventory
SLACK_INVENTORY_CHANNEL = os.environ.get("SLACK_INVENTORY_CHANNEL")
#inventory item edit channel
SLACK_ITEM_EDIT_CHANNEL = os.environ.get("SLACK_ITEM_EDIT_CHANNEL")
#inventory item delist channel
SLACK_ITEM_DELIST_CHANNEL = os.environ.get("SLACK_ITEM_DELIST_CHANNEL")

#Logistics Transport channel
SLACK_LOGISTICS_TRANSPORT_CHANNEL = os.environ.get("SLACK_LOGISTICS_TRANSPORT_CHANNEL")

#New cultivars
SLACK_NEW_CULTIVARS = os.environ.get("SLACK_NEW_CULTIVARS")

#eco farm bot
BOT_NAME = os.environ.get("BOT_NAME") 
BOT_ICON_URL= os.environ.get("BOT_ICON_URL")


# Admin Email
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
#Inventory Notification Email
NOTIFICATION_EMAIL_INVENTORY = os.environ.get("NOTIFICATION_EMAIL_INVENTORY")
#Logistics Transport Notification Email
NOTIFICATION_EMAIL_LOGISTICS_TRANSPORT = os.environ.get("NOTIFICATION_EMAIL_LOGISTICS_TRANSPORT")

# layouts
VENDOR_LAYOUT = json.loads(os.environ.get("VENDOR_LAYOUT"))
LEADS_LAYOUT = os.environ.get("LEADS_LAYOUT")
LICENSE_LAYOUT = os.environ.get("LICENSE_LAYOUT")

GOOGLEMAPS_API_KEY = os.environ.get('GOOGLEMAPS_API_KEY')
GOOGLEPLACES_API_KEY = os.environ.get('GOOGLEPLACES_API_KEY')
TWILIO_ACCOUNT = os.environ.get('TWILIO_ACCOUNT')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
DEFAULT_PHONE_NUMBER = os.environ.get('DEFAULT_PHONE_NUMBER')
TMP_DIR = os.environ.get('TMP_DIR')

#AWS Creds
AWS_CLIENT_ID = os.environ.get('AWS_CLIENT_ID')
AWS_CLIENT_SECRET = os.environ.get('AWS_CLIENT_SECRET')
AWS_BUCKET = os.environ.get('AWS_BUCKET')
AWS_REGION = os.environ.get('AWS_REGION')

# Authy Application Key
# You can get/create one here : https://www.twilio.com/console/authy/applications
AUTHY_ACCOUNT_SECURITY_API_KEY = os.environ.get('AUTHY_ACCOUNT_SECURITY_API_KEY')
AUTHY_APP_ID = os.environ.get('AUTHY_APP_ID')
AUTHY_APP_NAME = os.environ.get('AUTHY_APP_NAME')

AUTHY_USER_REGISTRATION_CALLBACK_SIGNING_KEY=os.environ.get('AUTHY_USER_REGISTRATION_CALLBACK_SIGNING_KEY')

BCC_APP_ID = os.environ.get('BCC_APP_ID')
BCC_APP_KEY = os.environ.get('BCC_APP_KEY')


ZOHO_CRM_URL = os.environ.get('ZOHO_CRM_URL')
CRM_ORGANIZATION_ID = os.environ.get('CRM_ORGANIZATION_ID')

#AWS for ckeditor
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')

NUMBER_OF_DAYS_TO_FETCH_INVENTORY = os.environ.get('NUMBER_OF_DAYS_TO_FETCH_INVENTORY')

ONBOARDING_DATA_FETCH_EMAIL_OVERRIDE = json.loads(os.environ.get("ONBOARDING_DATA_FETCH_EMAIL_OVERRIDE", "[]"))

BACKEND_DOMAIN_NAME = os.environ.get("BACKEND_DOMAIN_NAME")

CUSTOM_INVENTORY_WAREHOUSE_NAME = os.environ.get("CUSTOM_INVENTORY_WAREHOUSE_NAME")

INVENTORY_CSV_UPLOAD_FOLDER_ID = os.environ.get('INVENTORY_CSV_UPLOAD_FOLDER_ID')

INVENTORY_QR_UPLOAD_FOLDER_ID = os.environ.get('INVENTORY_QR_UPLOAD_FOLDER_ID')

IS_SANDBOX = os.environ.get('IS_SANDBOX')
ENV_PREFIX = os.environ.get('ENV_PREFIX')

TRACK_EVENT_SECRET_KEY = os.environ.get('TRACK_EVENT_SECRET_KEY')

#latest notification updated vars
ONBOARDING_ADMIN_EMAIL = os.environ.get('ONBOARDING_ADMIN_EMAIL')

SLACK_ONBOARDING_PROGRESS = os.environ.get('SLACK_ONBOARDING_PROGRESS')
SLACK_ONBOARDING_COMPLETED = os.environ.get('SLACK_ONBOARDING_COMPLETED')


INTERNAL_USER_DEFAULT_ORG_ID = os.environ.get('INTERNAL_USER_DEFAULT_ORG_ID')
BYPASS_VERIFICATION_FOR_EMAILS = json.loads(os.environ.get("BYPASS_VERIFICATION_FOR_EMAILS", "[]"))


# DRF API Logger
DRF_API_LOGGER_DATABASE = True
DRF_API_LOGGER_EXCLUDE_KEYS = ['password', 'token', 'access', 'refresh', 'Token']
DRF_API_LOGGER_DEFAULT_DATABASE = 'logger'
DRF_API_LOGGER_SKIP_URL_NAME = [
    'page-meta-list',
    'page-meta-detail',
    'page-meta-url-page-meta',
]

PASSWORDLESS_AUTH = {
    'PASSWORDLESS_AUTH_TYPES': ['EMAIL', 'PHONE'],
    'PASSWORDLESS_REGISTER_NEW_USERS': False,
    'PASSWORDLESS_USER_MOBILE_FIELD_NAME':'phone',
    'PASSWORDLESS_EMAIL_NOREPLY_ADDRESS': "Thrive Society <support@thrive-society.com>",
    'PASSWORDLESS_EMAIL_TOKEN_HTML_TEMPLATE_NAME': "passwordless.html",
    # 'PASSWORDLESS_MOBILE_MESSAGE':"Do not share this OTP with anyone.Use this code to log in with Thrive Society: %s",
    'PASSWORDLESS_MOBILE_MESSAGE':"Your verification code is %s",
    'PASSWORDLESS_MOBILE_NOREPLY_NUMBER':  os.environ.get('DEFAULT_PHONE_NUMBER'),
    'TWILIO_ACCOUNT_SID':os.environ.get('TWILIO_ACCOUNT'),
    'TWILIO_AUTH_TOKEN':os.environ.get('TWILIO_AUTH_TOKEN')    
}

AWS_OUTPUT_BUCKET = os.environ.get('AWS_OUTPUT_BUCKET')
INVENTORY_IMAGE_CROP_RATIO = float(os.environ.get('INVENTORY_IMAGE_CROP_RATIO'))

#Confia
CONFIA_ACCESS_KEY = os.environ.get('CONFIA_ACCESS_KEY')
CONFIA_ACCESS_SECRET = os.environ.get('CONFIA_ACCESS_SECRET')
CONFIA_BASIC_CALLBACK_USER_PW  = os.environ.get('CONFIA_BASIC_CALLBACK_USER_PW')
CONFIA_ACCESS_ID = os.environ.get('CONFIA_ACCESS_ID')
CONFIA_API_BASE_URL= os.environ.get('CONFIA_API_BASE_URL')

#Rapid API
RAPID_API_KEY = os.environ.get('RAPID_API_KEY')

#Box Sign
BOX_SIGN_W9_TEMPLATE_ID = os.environ.get('BOX_SIGN_W9_TEMPLATE_ID')
