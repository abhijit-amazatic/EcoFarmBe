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
        box_sign_obj.save()
        # if signer_decision !=
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
        # "signer_embed_url": signer_embed_url,
        "output_file_id": response['sign_files']['files'][0]['id'],
    }
    return info