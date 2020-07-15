from pyzoho.sign import (Sign, )
from integration.models import (Integration, )
from core.settings import (
    SIGN_CLIENT_ID,
    SIGN_CLIENT_SECRET,
    SIGN_REDIRECT_URI,
    SIGN_REFRESH_TOKEN,
)

def get_sign_obj():
    """
    Get zoho sign object.
    """
    try:
        token = Integration.objects.get(name='sign')
        access_token = token.access_token
        access_expiry = token.access_expiry
    except Integration.DoesNotExist:
        access_token = access_expiry = None
    sign_obj = Sign(
        client_id=SIGN_CLIENT_ID,
        client_secret=SIGN_CLIENT_SECRET,
        redirect_uri=SIGN_REDIRECT_URI,
        refresh_token=SIGN_REFRESH_TOKEN,
        access_token=access_token,
        access_expiry=access_expiry
    )
    if not access_token and not access_expiry:
        a = Integration.objects.update_or_create(
            name='sign',
            client_id=SIGN_CLIENT_ID,
            client_secret=SIGN_CLIENT_SECRET,
            refresh_token=SIGN_REFRESH_TOKEN,
            access_token=sign_obj.access_token,
            access_expiry=sign_obj.access_expiry[0]
            )
    return sign_obj

def create_estimate_document(
    file_obj,
    recipients,
    notes=None,
    expiry=10,
    reminder_period=5
    ):
    """
    create estimate in Zoho sign.
    """
    sign_obj = get_sign_obj()
    return sign_obj.create_document(
        file_obj=file_obj,
        recipients=recipients,
        notes=notes,
        expiry=expiry,
        reminder_period=reminder_period)

def submit_estimate_document(document_obj):
    """
    Submit estimate document for sign.
    """
    sign_obj = get_sign_obj()
    document_obj = document_obj.get('requests')
    return sign_obj.submit_document(document_obj['request_id'], document_obj)

def download_pdf(request_id):
    """
    Download estimate pdf.
    """
    sign_obj = get_sign_obj()
    return sign_obj.download_pdf(request_id)
    