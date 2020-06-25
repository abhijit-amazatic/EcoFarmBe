from datetime import (datetime, )
from .crm_format import (ACCOUNT_TYPES, )
from core.settings import (VENDOR_LAYOUT, LEADS_LAYOUT)

def get_vendor_contacts(key, value, obj, crm_obj):
    """
    Return different contacts from Zoho CRM.
    """
    contacts = {
            'Contact_1': 'Cultivation Manager',
            'Contact_2': 'Logistics Manager',
            'Contact_3': 'Q&A Manager',
            'Owner1': 'Owner'
        }
    response = dict()
    result = dict()
    for contact, position in contacts.items():
        c = obj.get(contact)
        if not c:
            continue
        if c['id'] in result.keys():
            final = result.get(c['id'])
        else:
            final = crm_obj.get_record('Contacts', c['id'])
            result[c['id']] = final
        if final['status_code'] == 200:
            final = {
                'employee_name': c['name'],
                'employee_email': final['response'][c['id']]['Email'],
                'phone': final['response'][c['id']]['Phone']
            }
            response[position] = final
        return response
    
def get_account_category(key, value, obj, crm_obj):
    """
    Return company category for account.
    """
    v = obj.get(value)
    if isinstance(v, list):
        l = list()
        for i in v:
            l.append(ACCOUNT_TYPES[i])
        return l
    else:
        return [ACCOUNT_TYPES[v]]
    
def get_cultivars_date(key, value, obj, crm_obj):
    """
    Return cultivar dates.
    """
    try:
        c = value.split('.')
        d = obj.get(c[0])
        e = c[1].split('_')
        if d:
            date = d[e[0]][int(e[1])-1]['harvest_date']
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
            return date
    except Exception as exc:
        return []

def get_layout(module, layout_name=None):
    """
    Return Layout for Zoho CRM.
    """
    if layout_name:
        layout = LEADS_LAYOUT
    if module == 'Vendors':
        return VENDOR_LAYOUT
    if module == 'Leads':
        return layout[layout_name]
    
def get_regex_checked(v):
    """
    Check if regex matches.
    """
    import re
    
    regex = 'po_[a-z_]*(.)(cultivars)'
    return re.search(regex, v)