import requests
from datetime import (datetime, )

import googlemaps
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator

from .crm_format import (ACCOUNT_TYPES, )
from core.settings import (
    VENDOR_LAYOUT, LEADS_LAYOUT, GOOGLEMAPS_API_KEY,
    GOOGLEPLACES_API_KEY,)

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

def parse_pdf(file_obj):
    resource_manager = PDFResourceManager()
    la_params = LAParams()
    device = PDFPageAggregator(resource_manager, laparams=la_params)
    interpreter = PDFPageInterpreter(resource_manager, device)
    try:
        pages = PDFPage.get_pages(file_obj)
        for page_number, page in enumerate(pages):
            interpreter.process_page(page)
            layout = device.get_result()
            for lobj in layout:
                if isinstance(lobj, LTTextBox):
                    x, y, text = lobj.bbox[0], lobj.bbox[3], lobj.get_text()
                    if text.strip() == 'Signature':
                        max_coord = page.mediabox
                        return round(x), round(max_coord[3]-y), page_number
        return None
    except Exception as exc:
        print('Estimate file donot have signature field', exc)
        return None

def get_distance(location_a, location_b):
    """
    Get distance between two locations.
    """
    try:
        if location_a and location_b:
            gmaps = googlemaps.Client(key=GOOGLEMAPS_API_KEY)
            response = gmaps.distance_matrix(location_a, location_b)['rows'][0]['elements'][0]
            return response
        response = {
            'code': 1
        }
        if not location_a and location_b:
            response['error'] = 'Both addresses are not valid.'
        if not location_a:
            response['error'] = 'location_a is not valid.'
        elif not location_b:
            response['error'] = 'location_b is not valid.'
        return response
    except googlemaps.exceptions.ApiError as exc:
        return {'code':1, 'Error': exc}

def get_places(address):
    """
    Get autocompleted address.
    """
    try:
        if address:
            result = list()
            gmaps = googlemaps.Client(key=GOOGLEPLACES_API_KEY)
            responses = gmaps.places_autocomplete(address)
            for response in responses:
                data = gmaps.places(response.get('description')).get('results')[0]
                result.append(data)
            return result
        return []
    except googlemaps.exceptions.ApiError as exc:
        return {'code':1, 'Error': exc}

def get_cultivars_date(key, value, obj, crm_obj):
    """
    Return cultivar dates.
    """
    try:
        e = value.split('_')
        if obj:
            date = obj[e[0]][int(e[1])-1]['harvest_date']
            date = datetime.strptime(date, '%Y-%m-%d')
            return date
    except Exception as exc:
        return []

def get_overview_field(key, value, obj, crm_obj):
    """
    Return overview field.
    """
    is_full_season = obj.get('co.full_season')
    is_autoflower = obj.get('co.autoflower')
    v = value.split('.')
    overview_name = v[0]
    dictionary = obj.get(overview_name + '.overview')
    field = v[2]
    if is_full_season == False and is_autoflower == True:
        index = 0
    else:
        index = int(v[1])
    if is_autoflower == False and index == 1:
        return None
    if dictionary:
        if 'cultivars' in field:
            return get_cultivars_date(key, field, dictionary[index], crm_obj)
        else:
            return dictionary[index].get(field)
    return None