from datetime import (datetime, timedelta, )
from core.settings import (
    BOOKS_CLIENT_ID,
    BOOKS_CLIENT_SECRET,
    BOOKS_ORGANIZATION_ID,
    BOOKS_REDIRECT_URI,
    BOOKS_REFRESH_TOKEN
)
from pyzoho.books import (Books, )
from .models import (Integration, )


def get_books_obj():
    """
    Get Pyzoho books object.
    """
    try:
        token = Integration.objects.get(name='books')
        access_token = token.access_token
        access_expiry = token.access_expiry
    except Integration.DoesNotExist:
        access_token = access_expiry = None
    books_obj = Books(
        client_id=BOOKS_CLIENT_ID,
        client_secret=BOOKS_CLIENT_SECRET,
        redirect_uri=BOOKS_REDIRECT_URI,
        organization_id=BOOKS_ORGANIZATION_ID,
        refresh_token=BOOKS_REFRESH_TOKEN
    )
    if books_obj._refreshed:
        Integration.objects.update_or_create(
            name='books',
            client_id=BOOKS_CLIENT_ID,
            client_secret=BOOKS_CLIENT_SECRET,
            refresh_token=BOOKS_REFRESH_TOKEN,
            access_token=books_obj.access_token,
            access_expiry=books_obj.access_expiry
    )
    return books_obj
        
def create_contact(data, params=None):
    """
    Create contact in Zoho Books.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.create_contact(data, parameters=params)

def create_estimate(data, params=None):
    """
    Create estimate in Zoho Books.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    return estimate_obj.create_estimate(data, parameters=params)

def get_estimate(estimate_id, params=None):
    """
    Get an estimate.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    return estimate_obj.get_estimate(estimate_id, parameters=params)

def list_estimates(params=None):
    """
    List estimates.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    return estimate_obj.list_estimates(parameters=params)

def get_contact(contact_id, params=None):
    """
    Get contact.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.get_contact(contact_id, parameters=params)

def list_contacts(params=None):
    """
    List contact.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.list_contacts(parameters=params)