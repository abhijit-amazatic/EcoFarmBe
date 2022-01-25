from django.core.exceptions import ObjectDoesNotExist

from brand.models import LicenseProfile
from .box import(
    get_shared_link,
    get_sign_request,

    BoxException,
    BoxAPIException,
)


def box_sign_update_to_db(box_sign_obj):
    signer_decision = box_sign_obj.signer_decision
    try:
        response = get_sign_request(box_sign_obj.request_id)
    except BoxAPIException as e:
        response = e.network_response.json()
    else:
        update_data = {
            **get_box_sign_request_info(response),
            "status": response['status'],
            "response": response,
        }
        box_sign_obj.__dict__.update(update_data)
        if box_sign_obj.signer_decision == 'signed' and  signer_decision != 'signed':
            if box_sign_obj.doc_type.name == 'agreement':
                try:
                    profile = box_sign_obj.license.license_profile
                except ObjectDoesNotExist:
                    profile = LicenseProfile.objects.create(license=box_sign_obj.license)

                profile.agreement_signed = True
                profile.agreement_link = get_shared_link(box_sign_obj.output_file_id)
                profile.save()
                if box_sign_obj.license.status == 'in_progress':
                    box_sign_obj.license.status = 'completed'
                    box_sign_obj.license.step = '1'
                    box_sign_obj.license.save()

            elif box_sign_obj.doc_type.name == 'w9':
                output_file_id = box_sign_obj.output_file_id
                box_sign_obj.license.uploaded_w9_to = get_shared_link(output_file_id)
                box_sign_obj.license.save()
        box_sign_obj.save()
    return box_sign_obj

def get_box_sign_request_info(response):
    signer_status = ''
    signer_embed_url = None
    for signer in response['signers']:
        if signer['order'] == 1:
            if signer['signer_decision']:
                signer_status = signer['signer_decision'].get('type', '')
            signer_embed_url = signer['embed_url']
            break

    info = {
        "signer_decision": signer_status,
        "signer_embed_url": signer_embed_url,
        "output_file_id": response['sign_files']['files'][0]['id'],
    }
    return info
