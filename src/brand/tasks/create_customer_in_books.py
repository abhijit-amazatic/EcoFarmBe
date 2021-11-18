import sys
import traceback
from django.conf import settings

from core.celery import app
from integration.books import (
    get_books_obj,
    get_format_dict,
    create_contact,
    update_contact,
    search_contact_by_field,
)

from ..models import (
    License
)



CRM_PROFILES_MAP = {
    'customer': 'account',
    'vendor': 'vendor',
}

@app.task(queue="general")
def create_customer_in_books_task(id=None, is_single_user=False, params={}):
    """
    Create customer in the Zoho books.
    """
    final_response_list = list()

    if id:
        qs = License.objects.filter(id=id)
    else:
        qs = License.objects.filter(is_updated_in_crm=False)

    for license_obj in qs:
        response_dict = dict()
        request = dict()
        request.update(license_obj.__dict__)
        request.update(license_obj.license_profile.__dict__)
        try:
            request.update(license_obj.profile_contact.profile_contact_details)
        except Exception:
            pass

        for contact_type in ['vendor', 'customer']:
            crm_profile_id = request.get(f'zoho_crm_{CRM_PROFILES_MAP.get(contact_type)}_id')
            response_dict[contact_type] = dict()
            for org_name in ('efd', 'efl', 'efn'):
                books_name = f'books_{org_name}'
                books_obj = get_books_obj(f'books_{org_name}')
                contact_obj = books_obj.Contacts()
                contact_id = db_contact_id = request.get(f'zoho_books_{contact_type}_ids', {}).get(org_name, '')

                response_dict[contact_type][org_name] = dict()
                if settings.PRODUCTION:
                    if crm_profile_id:
                        response = {}
                        if contact_type == 'customer':
                            response = contact_obj.import_customer_using_crm_account_id(crm_profile_id)
                        else:
                            response = contact_obj.import_vendor_using_crm_vendor_id(crm_profile_id)
                        if response and response.get('code') == 0:
                            contact_id = response.get('data', {}).get('customer_id')
                        response_dict[contact_type][org_name]['CRM import'] = response
                        if not contact_id:
                            r = contact_obj.get_contact_using_crm_account_id(crm_profile_id)
                            try:
                                if r and r.get('code') == 0:
                                    for c in r.get('contacts', []):
                                        if c.get('contact_type') == contact_type:
                                            if c.get('contact_id'):
                                                contact_id = c.get('contact_id')
                            except Exception as e:
                                print(e)
                    else:
                        response_dict[contact_type][org_name]['Error'] = f'Skiped, no CRM {CRM_PROFILES_MAP.get(contact_type)} id present in db.'

                    if contact_id:
                        parsed_contact_persons = parse_books_fields("contact_persons", 'employees', request)
                        contact_persons_update = get_contact_persons_to_update(books_name, contact_id, parsed_contact_persons)
                        update_data = {'contact_id': contact_id, 'contact_persons': contact_persons_update }
                        response = update_contact(books_name, update_data, params=params)
                        if response.get('code'):
                            print('Error while updating contact persons.')
                            print(f'books_name: {books_name}')
                            print('data: ', update_data)
                            print('response: ', response)
                            response_dict[contact_type][org_name]['contact persons update'] = {
                                'data': update_data,
                                'response': response,
                            }
                        else:
                            response_dict[contact_type][org_name]['contact persons update'] = {
                                'data': update_data,
                                'response': "OK",
                            }
                else:
                    try:
                        record_dict = parse_books_customer(request)
                        record_dict['contact_type'] = contact_type
                        if not contact_id:
                            resp = search_contact_by_field(contact_obj, 'cf_client_id', request.get('client_id', ''), contact_type)
                            if resp and resp.get('contact_id'):
                                contact_id = resp.get('contact_id')
                            if not contact_id:
                                resp = search_contact_by_field(contact_obj, 'contact_name', request.get('name', ''), contact_type)
                                # resp = search_contact(books_obj, request.get('legal_business_name', ''), contact_type)
                                if resp and resp.get('contact_id'):
                                    contact_id = resp.get('contact_id')

                        if contact_id:
                            record_dict['contact_persons'] = get_contact_persons_to_update(books_name, contact_id, record_dict.get('contact_persons', []))
                            record_dict['contact_id'] = contact_id
                            response = update_contact(books_name, record_dict, params=params)
                        else:
                            if 'contact_id' in record_dict:
                                record_dict.pop('contact_id')
                            response = create_contact(books_name, record_dict, params=params)
                            contact_id = response.get('contact_id')
 
                        if response.get('code'):
                            response_dict[contact_type][org_name] = {
                                    'data': record_dict,
                                    'response': response,
                                }
                        elif contact_id == response.get('contact_id'):
                            response_dict[contact_type][org_name] = 'OK'


                    except Exception as exc:
                        print(exc)
                        debug_vars = ('record_dict', 'contact_id', 'resp')
                        locals_data = {k: v for k, v in locals().items() if k in debug_vars}
                        exc_info = sys.exc_info()
                        e = ''.join(traceback.format_exception(*exc_info))
                        response_dict[contact_type][org_name]['exception'] = e
                        response_dict[contact_type][org_name]['local_vars'] = locals_data

                if contact_id:
                    if not db_contact_id or db_contact_id != contact_id:
                        license_obj.refresh_from_db()
                        license_obj.__dict__[f'zoho_books_{contact_type}_ids'].update({org_name: contact_id})
                        license_obj.save()

        license_obj.refresh_from_db()
        license_obj.books_output = response_dict
        license_obj.save()
        final_response_list.append(response_dict)

    return final_response_list

def get_contact_persons_to_update(books_name, contact_id, parsed_contact_persons):
    books_contact_persons = []
    books_obj = get_books_obj(books_name)
    contact_persons_obj = books_obj.ContactPersons()
    result = contact_persons_obj.get_contact_person(contact_id)
    if result.get('code') == 0:
        books_contact_persons = [
            {k: v for k, v in c.items() if k in ('contact_person_id', 'first_name', 'last_name', 'email', 'phone', 'designation')}
            for c in result.get('contact_persons', [])
        ]

    parsed_contact_persons = {c.get('email'): c for c in parsed_contact_persons}
    updated_contact_persons = []

    for contact_person in books_contact_persons:
        if contact_person.get('email') in parsed_contact_persons:
            c = parsed_contact_persons.pop(contact_person.get('email'))
            contact_person.update({k:v for k, v in c.items() if v})
        updated_contact_persons.append(contact_person)
    updated_contact_persons += list(parsed_contact_persons.values())

    return updated_contact_persons

def parse_books_customer(request):
    books_dict = get_format_dict('Books_Customer')
    # try:
    #     if not is_update:
    #         del books_dict['contact_id']
    #     else:
    #         del books_dict['contact_persons']
    # except KeyError:
    #     pass
    record_dict = dict()
    record_dict['custom_fields'] = []
    for k, v in books_dict.items():
        if v.endswith('_parse'):
            v = v.split('_parse')[0]
            v = parse_books_fields(k, v, request)
        else:
            v = request.get(v)
        if k.startswith('cf_'):
            record_dict['custom_fields'].append({'api_name': k, 'value': v})
        else:
            record_dict[k] = v
    return record_dict

def parse_books_fields(k, v, request):
    """
    Parse books fields.
    """
    value = request.get(v, None)
    if v in ['billing_address', 'mailing_address']:
        return {
            'address': value.get('street'),
            'street2': value.get('street_line_2'),
            # 'state_code': value.get('state'),
            'city': value.get('city'),
            'state': value.get('state'),
            'zip': value.get('zip_code'),
            'country': value.get('country'),
            'phone': value.get('phone')
        }
    elif v == 'employees':
        contact_persons = dict()
        for value in request.get(v, None):
            email = value.get('employee_email')
            if email:
                role = ''
                roles = value.get('roles')
                if roles and isinstance(roles, list):
                    role = roles[0]
                if email not in contact_persons:
                    first_name = ''
                    last_name = ''
                    full_name = value.get('employee_name')
                    if full_name and isinstance(full_name, str):
                        full_name = full_name.split()
                        first_name = ' '.join(full_name[0:-1])
                        last_name = full_name[-1]
                    contact_persons[email] = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': value.get('employee_email'),
                        'phone': value.get('phone'),
                        # 'mobile': value.get('phone'),
                        'designation': role,
                        # 'department': value.get('department'),
                        # 'is_primary_contact': is_primary,
                        # 'skype': value.get('skype'),
                    }
                else:
                    if role and not contact_persons[email]['designation']:
                        contact_persons[email]['designation'] = role
        return list(contact_persons.values())
    elif v == 'contact_type':
        if request.get('is_buyer'):
            return 'customer'
        elif request.get('is_seller'):
            return 'vendor'
