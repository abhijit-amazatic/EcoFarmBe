from core import settings


OAUTH_SERVICE_INFO = {
    'zoho': {
        # 'client_id': settings.ZOHO_CLIENT_ID,
        # 'client_secret': settings.ZOHO_CLIENT_SECRET,
        # 'redirect_uri': settings.ZOHO_REDIRECT_URI,
        'auth_url': 'https://accounts.zoho.com/oauth/v2/auth',
        'auth_code_callback_kw_name' : 'code',
        'access_token_url': 'https://accounts.zoho.com/oauth/v2/token',
        'refresh_token_url': 'https://accounts.zoho.com/oauth/v2/token',
        'revoke_token_url': 'https://accounts.zoho.com/oauth/v2/token/revoke',
        # 'revoke_token_url_kw_name' : 'token',
        'params': {
            'redirect_uri': {
                'response_type': 'code',
                'access_type':   'offline',
                'prompt':        'Consent',
                'client_id': '',
                'redirect_uri': '',
                'state': '',
                'scope': ''
            },
            'authenticate': {
                'grant_type': 'authorization_code',
                'client_id': '',
                'client_secret': '',
                'redirect_uri': '',
                'code': '',
            },
            'revoke_token': {
                'token': '',
            },
        },

    },
    'box': {
        'client_id': settings.BOX_CLIENT_ID,
        'client_secret': settings.BOX_CLIENT_SECRET,
        # 'redirect_uri': settings.BOX_CLIENT_SECRET,
        'auth_url': 'https://account.box.com/api/oauth2/authorize',
        'access_token_url': 'https://api.box.com/oauth2/token',
        'refresh_token_url': 'https://api.box.com/oauth2/token',
        'auth_code_callback_kw_name' : 'code',
        'revoke_token_url': 'https://api.box.com/oauth2/revoke',
        # 'revoke_token_url_kw_name' : 'token',
        'params': {
            'redirect_uri': {
                'response_type': 'code',
                'client_id': '',
                'redirect_uri': '',
                'state': '',
                'scope': ''
            },
            'authenticate': {
                'grant_type': 'authorization_code',
                'client_id': '',
                'client_secret': '',
                'code': '',
            },
            'revoke_token': {
                'client_id': '',
                'client_secret': '',
                'token': '',
            },
        },
    },
}

INTEGRATION_OAUTH_MAP = {
    'crm': {
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL,ZohoCRM.org.ALL,ZohoCRM.coql.READ',
        'client_id': settings.PYZOHO_CONFIG['client_id'],
        'client_secret' : settings.PYZOHO_CONFIG['client_secret'],
        'redirect_uri': settings.PYZOHO_CONFIG['redirect_uri'],
    },
    'books': {
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoBooks.fullaccess.all',
        'client_id': settings.BOOKS_CLIENT_ID,
        'client_secret' : settings.BOOKS_CLIENT_SECRET,
        'redirect_uri': settings.BOOKS_REDIRECT_URI,
    },
    'books_efd': {
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoBooks.fullaccess.all',
        'client_id': settings.BOOKS_CLIENT_ID,
        'client_secret' : settings.BOOKS_CLIENT_SECRET,
        'redirect_uri': settings.BOOKS_REDIRECT_URI,
    },
    'books_efl':{
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoBooks.fullaccess.all',
        'client_id': settings.BOOKS_CLIENT_ID,
        'client_secret' : settings.BOOKS_CLIENT_SECRET,
        'redirect_uri': settings.BOOKS_REDIRECT_URI,
    },
    'books_efn':{
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoBooks.fullaccess.all',
        'client_id': settings.BOOKS_CLIENT_ID,
        'client_secret' : settings.BOOKS_CLIENT_SECRET,
        'redirect_uri': settings.BOOKS_REDIRECT_URI,
    },
    'inventory':{
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoInventory.fullaccess.all',
        'client_id': settings.INVENTORY_CLIENT_ID,
        'client_secret' : settings.INVENTORY_CLIENT_SECRET,
        'redirect_uri': settings.INVENTORY_REDIRECT_URI,
    },
    'inventory_efd':{
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoInventory.fullaccess.all',
        'client_id': settings.INVENTORY_CLIENT_ID,
        'client_secret' : settings.INVENTORY_CLIENT_SECRET,
        'redirect_uri': settings.INVENTORY_REDIRECT_URI,
    },
    'inventory_efl':{
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoInventory.fullaccess.all',
        'client_id': settings.INVENTORY_CLIENT_ID,
        'client_secret' : settings.INVENTORY_CLIENT_SECRET,
        'redirect_uri': settings.INVENTORY_REDIRECT_URI,
    },
    'inventory_efn':{
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoInventory.fullaccess.all',
        'client_id': settings.INVENTORY_CLIENT_ID,
        'client_secret' : settings.INVENTORY_CLIENT_SECRET,
        'redirect_uri': settings.INVENTORY_REDIRECT_URI,
    },
    'sign':{
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': 'ZohoSign.documents.all',
        'client_id': settings.SIGN_CLIENT_ID,
        'client_secret' : settings.SIGN_CLIENT_SECRET,
        'redirect_uri': settings.SIGN_REDIRECT_URI,
    },
    'campaign':{
        **OAUTH_SERVICE_INFO['zoho'],
        'scope': '',
        'client_id': settings.CAMPAIGN_CLIENT_ID,
        'client_secret' : settings.CAMPAIGN_CLIENT_SECRET,
        'redirect_uri': settings.CAMPAIGN_REDIRECT_URI,

    },
    # 'box':{
    #     **OAUTH_SERVICE_INFO['box'],
    #     'scope': 'root_readwrite,manage_app_users,manage_groups,manage_enterprise_properties',
    #     # 'scope': 'root_readonly',
    # },
}
