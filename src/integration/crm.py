from pyzoho import CRM
from core.settings import (PYZOHO_CONFIG,
    PYZOHO_REFRESH_TOKEN,
    PYZOHO_USER_IDENTIFIER)

def create_record(module, data):
    crm_obj = CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER)
    contact_dict = dict()
    contact_fields = [i.lower().replace(' ', '_') for i in crm_obj.get_fields(module).keys()]
    for k, v in data.items():
        if k in contact_fields:
            contact_dict[k.title()] = v
    response = crm_obj.insert_record(module, contact_dict)
    return response

def search_query(module, query, criteria):
    crm_obj = CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER)
    return crm_obj.search_record(module, query, criteria)