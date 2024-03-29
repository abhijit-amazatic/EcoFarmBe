import hashlib
import zipfile
from io import BytesIO
from pyzoho.sign import (Sign, )
from integration.models import (Integration, )
from core.settings import (
    SIGN_CLIENT_ID,
    SIGN_CLIENT_SECRET,
    SIGN_REDIRECT_URI,
    SIGN_REFRESH_TOKEN,
    SIGN_HOST_URL,
)
from integration.box import (create_folder, upload_file_stream,)
from .utils import (parse_pdf, )
from core.celery import app

def get_sign_obj():
    """
    Get zoho sign object.
    """
    try:
        token = Integration.objects.get(name='sign')
        access_token = token.access_token
        access_expiry = token.access_expiry
        refresh_token = token.refresh_token
    except Integration.DoesNotExist:
        access_token = access_expiry = None
        refresh_token = SIGN_REFRESH_TOKEN
    sign_obj = Sign(
        client_id=SIGN_CLIENT_ID,
        client_secret=SIGN_CLIENT_SECRET,
        redirect_uri=SIGN_REDIRECT_URI,
        refresh_token=refresh_token,
        access_token=access_token,
        access_expiry=access_expiry,
        host=SIGN_HOST_URL
    )
    if sign_obj._refreshed:
        a = Integration.objects.update_or_create(
            name='sign',
            defaults={
                "client_id":SIGN_CLIENT_ID,
                "client_secret":SIGN_CLIENT_SECRET,
                "refresh_token":sign_obj.refresh_token,
                "access_token":sign_obj.access_token,
                "access_expiry":sign_obj.access_expiry[0]
                }
            )
    return sign_obj

def get_document(request_id):
    """
    Get document from Zoho sign.
    """
    sign_obj = get_sign_obj()
    return sign_obj.get_document(request_id)

def create_estimate_document(
    file_obj,
    recipients,
    notes=None,
    expiry=10,
    reminder_period=5,
    notify_addresses=None
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
        reminder_period=reminder_period,
        notify_addresses=notify_addresses)

def submit_estimate_document(document_obj, x, y, page_number):
    """
    Submit estimate document for sign.
    """
    sign_obj = get_sign_obj()
    document_obj = document_obj.get('requests')
    return sign_obj.submit_document(
        document_obj['request_id'],
        document_obj,
        x, y,
        page_number)

def download_pdf(request_id):
    """
    Download estimate pdf.
    """
    sign_obj = get_sign_obj()
    return sign_obj.download_pdf(request_id)

@app.task(queue="urgent")
def upload_pdf_box(request_id, folder_id, file_name, is_agreement=False):
    """
    Upload document to box.
    """
    file_obj_o = download_pdf(request_id)
    if is_agreement:
        file_obj = BytesIO(file_obj_o)
        try:
            zip_file = zipfile.ZipFile(file_obj)
            for f in zip_file.namelist():
                if file_name in f:
                    file_name = f
            file_obj_o = zip_file.open(file_name).read()
        except Exception:
            file_obj = BytesIO(file_obj_o)
            file_obj_o = file_obj.read()
    # box_sha1 = hashlib.sha1(file_obj).hexdigest()
    file_obj = BytesIO(file_obj_o)
    new_file = upload_file_stream(folder_id, file_obj, file_name)
    try:
        return new_file.id
    except AttributeError:
        return new_file
    # if box_sha1 != new_file.sha1:
    #     print('Error in upload pdf to box wrong checksum', request_id)
    
def submit_estimate(
    file_obj,
    recipients,
    notes=None,
    expiry=10,
    reminder_period=5,
    notify_addresses=None):
    """
    Create document and submit for signature.
    """
    document_obj = create_estimate_document(
        file_obj,
        recipients,
        notes,
        expiry,
        reminder_period,
        notify_addresses
    )
    x, y, page_number = parse_pdf(file_obj[0][1])
    x, y = x+42, y-5
    response = submit_estimate_document(document_obj, x, y, page_number)
    if response['code'] == 0:
        for action in response['requests']['actions']:
            if action.get('action_type') == 'SIGN':
                action_id = action.get('action_id')
        return get_embedded_url_from_sign(
            response['requests']['request_id'],
            action_id
            )
    return response

def get_embedded_url_from_sign(request_id, action_id):
    """
    Return embedded url to sign.
    """
    sign_obj = get_sign_obj()
    response = sign_obj.get_embedded_url(request_id, action_id)
    if response['code'] == 0:
        response['request_id'] = request_id
        response['action_id'] = action_id
        return response
    return response

def get_template(template_id):
    """
    Get template details.
    """
    sign_obj = get_sign_obj()
    return sign_obj.get_template(template_id)

def send_template(
    template_id,
    recipients,
    licenses=[],
    legal_business_names=[],
    EIN=None, SSN=None, business_structure=[],
    license_owner_name=None, premise_address=None,
    premise_state=None, premise_city=None, premise_zip=None,
    license_owner_email=None):
    """
    Send template to sign.
    """
    sign_obj = get_sign_obj()
    data = get_template(template_id)
    if data.get('templates'):
        response = sign_obj.send_document_using_template(
            template_id,
            data['templates'],
            recipients,
            licenses,
            legal_business_names,
            EIN, SSN, business_structure,
            license_owner_name, premise_address,
            premise_state, premise_city, premise_zip,
            license_owner_email
        )
        print('In send_template method response===>', response)
        if response['code'] == 0:
            return get_embedded_url_from_sign(
                response['requests']['request_id'],
                response['requests']['actions'][0]['action_id']
            )
        return response
    return {'code': 1,
            'error': data}
