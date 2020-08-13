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

def upload_pdf_box(request_id, folder_id, file_name):
    """
    Upload document to box.
    """
    file_obj = download_pdf(request_id)
    file_obj = BytesIO(file_obj)
    new_file = upload_file_stream(folder_id, file_obj, file_name)
    
def submit_estimate(
    file_obj,
    recipients,
    notes=None,
    expiry=10,
    reminder_period=5):
    """
    Create document and submit for signature.
    """
    document_obj = create_estimate_document(
        file_obj,
        recipients,
        notes,
        expiry,
        reminder_period
    )
    x, y, page_number = parse_pdf(file_obj[0][1])
    x, y = x+42, y-5
    response = submit_estimate_document(document_obj, x, y, page_number)
    if response['code'] == 0:
        return get_embedded_url_from_sign(
            response['requests']['request_id'],
            response['requests']['actions'][0]['action_id'])

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

def get_template(template_id):
    """
    Get template details.
    """
    sign_obj = get_sign_obj()
    return sign_obj.get_template(template_id)

# def send_template(
#     template_id,
#     recipients,
#     licenses):
#     """
#     Send template to sign.
#     """
#     sign_obj = get_sign_obj()
#     data = get_template(template_id)
#     if data.get('templates'):
#         response = sign_obj.send_document_using_template(
#             template_id,
#             data['templates'],
#             recipients,
#             licenses
#         )
#         if response['code'] == 0:
#             return get_embedded_url_from_sign(
#                 response['requests']['request_id'],
#                 response['requests']['actions'][0]['action_id']
#             )
#         return response
#     return {'code': 1,
#             'error': data}