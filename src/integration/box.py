import os
import json
from io import BytesIO
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from .models import Integration
from boxsdk import (OAuth2, Client, JWTAuth)
from boxsdk.exception import (BoxOAuthException,
                              BoxException, BoxAPIException)
from core.celery import app
from core.settings import (
    REDIS_URL,
    BOX_CLIENT_ID,
    BOX_CLIENT_SECRET,
    BOX_REFRESH_TOKEN,
    BOX_ACCESS_TOKEN,
    FARM_FOLDER_ID,
    BOX_JWT_DICT,
    BOX_JWT_USER,
    INVENTORY_BOX_ID)

from brand.models import License


def get_redis_obj():
    """
    Return redis object.
    """
    import redis

    return redis.from_url(REDIS_URL)


def set_tokens(access_token, refresh_token):
    """
    Store box tokens in redis.Callable method can be
    passed to Box OAuth2 as a parameter to store token
    automatically.

    @param access_token: Access token to store.
    @param refresh_token: Refresh token to store.
    """
    db = get_redis_obj()
    redis_value = json.dumps(
        {'access_token': access_token, 'refresh_token': refresh_token})
    db.set("box_api_tokens", redis_value)


def set_tokens_db(access_token, refresh_token):
    """
    Store box tokens in database.Callable method can be
    passed to Box OAuth2 as a parameter to store token
    automatically.

    @param access_token: Access token to store.
    @param refresh_token: Refresh token to store.
    """
    _, created = Integration.objects.update_or_create(
        name='box',
        defaults={
            'access_token': access_token,
            'refresh_token': refresh_token}
    )


def get_oauth2_obj():
    """
    Return Box OAuth2 object.

    @return boxsdk.OAuth2 object.
    """
    try:
        try:
            obj = Integration.objects.get(name='box')
            access_token = obj.access_token
            refresh_token = obj.refresh_token
        except Integration.DoesNotExist:
            access_token = BOX_ACCESS_TOKEN
            refresh_token = BOX_REFRESH_TOKEN
        oauth = OAuth2(
            client_id=BOX_CLIENT_ID,
            client_secret=BOX_CLIENT_SECRET,
            access_token=access_token,
            refresh_token=refresh_token,
            store_tokens=set_tokens_db
        )
        return oauth
    except BoxOAuthException as exc:
        print(exc)
        return {'error': exc}


def get_box_tokens():
    """
    DO NOT MODIFY THIE METHOD.
        - Method is used in Zoho CRM to upload file to box.

    @return dict object.
    """
    try:
        oauth2 = get_oauth2_obj()
        client = Client(oauth2)
        client.user().get()
        return {'status': 'success', 'access_token': oauth2.access_token, 'refresh_token': oauth2._refresh_token}
    except BoxException as exc:
        return {'status_code': 'error', 'error': exc}


def get_box_client():
    """
    Return Box client.

    @return boxsdk.Client object.
    """
    return get_jwt_client()
    # obj = get_oauth2_obj()
    # return Client(obj)


def get_jwt_client():
    """
    Return box jwt object.
    """
    try:
        jwt_dict = json.loads(BOX_JWT_DICT)
    except Exception:
        jwt_dict = BOX_JWT_DICT
    auth = JWTAuth.from_settings_dictionary(jwt_dict)
    client = Client(auth)
    service_account = client.user().get()
    user = client.user(user_id=BOX_JWT_USER)
    return client.as_user(user)

# -------------------------------------
# Box functions for folder.
# -------------------------------------


def get_folder_obj(folder_id):
    """
    Return box folder object.

    @param folder_id: Box folder id.
    @return boxsdk.Folder object.
    """
    client = get_box_client()
    return client.folder(folder_id=folder_id).get()


def get_folder_information(folder_id):
    """
    Return box folder information.

    @param folder_id: Box folder id.
    @return dict object.
    """
    folder = get_folder_obj(folder_id)
    return parse_folder(folder)


def create_folder(parent_folder_id, new_folder_name):
    """
    Create subfolder in parent folder.

    @param parent_folder_id: Parent folder id.
    @param new_folder_name: Name of new folder to create.
    @return folder_id.
    """
    try:
        a = get_folder_obj(
            parent_folder_id).create_subfolder(
                new_folder_name
        ).id
        return a
    except BoxException as exc:
        if exc.context_info.get('conflicts'):
            return exc.context_info.get('conflicts')[0]['id']


# def upload_from_tmp_dir():
#     tmp = settings.TMP_DIR if settings.TMP_DIR else '/tmp/'
#     files = os.listdir(tmp)
#     files = [x for x in files if '.pdf' in x]
#     for _file in files:
#         try:
#             license = License.objects.get(
#                 legal_business_name=_file.split('-')[1])
#             if 'license' in _file.split('-')[-1]:
#                 license.uploaded_license_to = upload_file(
#                     '111282192684', tmp+_file)
#             elif 'seller-permit' in _file.split('-')[-1]:
#                 license.uploaded_sellers_permit_to = upload_file(
#                     '111282192684', tmp+_file)
#             license.save()
#             os.remove(tmp+_file)
#         except License.DoesNotExists:
#             pass


def upload_file(folder_id, file_path, file_name, license_id=None, key=None):
    """
    Upload file to parent folder.

    @param folder_id: Box folder id.
    @param file_path: file path to upload.
    @param file_name: name of the file
    @param license_id: license to update 
    @return file id.
    """
    client = get_box_client()
    box_obj = client.folder(folder_id).upload(file_path, file_name=file_name)
    if license_id:
        License.objects.filter(id=license_id).update(**{key: box_obj.id})


def upload_file_stream(folder_id, stream, file_name):
    """
    Upload file using live stream.
    """
    try:
        client = get_box_client()
        return client.folder(folder_id).upload_stream(stream, file_name)
    except BoxException as exc:
        if exc.context_info.get('conflicts'):
            return exc.context_info.get('conflicts')['id']


def get_folder_items(folder_id):
    """
    Return sub-directories of folder.

    @param folder_id: Box folder id.
    @return dict object.
    """
    folders = get_folder_obj(folder_id).item_collection['entries']
    response = dict()
    for folder in folders:
        response[folder.object_id] = folder.name
    return response


def get_client_folder_id(client_folder_name):
    """
    upload file to specific client folder on box.
    """
    dirs = get_folder_items(FARM_FOLDER_ID)
    for k, v in dirs.items():
        if v.lower() == client_folder_name.lower():
            return k
        else:
            return create_folder(FARM_FOLDER_ID, client_folder_name)

def get_inventory_folder_id(client_folder_name):
    """
    upload file to specific client folder on box.
    """
    dirs = get_folder_items(INVENTORY_BOX_ID)
    for k, v in dirs.items():
        if v.lower() == client_folder_name.lower():
            return k
        else:
            return create_folder(INVENTORY_BOX_ID, client_folder_name)

def search(parent_dir, name):
    """
    Search folder/file in folder.
    """
    dirs = get_folder_items(parent_dir)
    for k, v in dirs.items():
        if v.lower() == name.lower():
            return k


def parse_folder(folder):
    """
    Parse folder information from api.

    @param boxsdk Folder object.
    @return dict object.
    """
    response = dict()
    response["id"] = folder.object_id
    response["type"] = folder.object_type
    response["Owner"] = {"id": folder.owned_by.id,
                         "user": folder.owned_by.name}
    response["name"] = folder.name
    response["parent"] = folder.parent
    response["items"] = folder.item_collection
    response["shared_link"] = folder.get_shared_link()
    return response

# -------------------------------------
# Box functions for files.
# -------------------------------------


def get_file_obj(file_id):
    """
    Return box file object.

    @param file_id: Box file id.
    @return boxsdk File object.
    """
    client = get_box_client()
    return client.file(file_id).get()


def get_file_information(file_id):
    """
    Return file information.

    @param file_id: Box file id.
    @return dict object.
    """
    file_ = get_file_obj(file_id)
    return parse_file(file_)


def update_file_version(file_id, file_path):
    """
    Update latest version of file.

    @param file_id: Box file id.
    @param file_path: file path to update.
    @return file id.
    """
    client = get_box_client()
    return client.file(file_id).update_contents(file_path)


def parse_file(file_obj):
    """
    Paarse file from box.

    @param file_obj: boxsdk File object
    @return dict object
    """
    response = dict()
    response["id"] = file_obj.object_id
    response["name"] = file_obj.name
    response["type"] = file_obj.object_type
    response["ownder"] = {"id": file_obj.owned_by.id,
                          "user": file_obj.owned_by.name}
    response["parent"] = file_obj.parent
    response["shared_link"] = file_obj.get_shared_link_download_url()
    return response


def get_shared_link(file_id, access='open', unshared_at=None, allow_download=None, allow_preview=True):
    """
    Get shareable link for file
    """
    client = get_box_client()
    return client.file(file_id).get_shared_link(
        access=access,
        allow_download=allow_download,
        allow_preview=allow_preview)


def move_file(file_id, destination_folder_id):
    """
    Move file into destination folder.
    """
    client = get_box_client()
    file_to_move = client.file(file_id)
    destination_folder = client.folder(destination_folder_id)
    moved_file = file_to_move.move(destination_folder)
    return moved_file


def delete_file(file_id):
    """
    Delete file from box.
    """
    try:
        client = get_box_client()
        return client.file(file_id=file_id).delete()
    except BoxException as exc:
        return {'status': 1, 'error': 'Not found'}


def get_embed_url(file_id):
    """
    Return embed url for file.
    """
    client = get_box_client()
    return client.file(file_id).get_embed_url()


def get_download_url(file_id):
    """
    Return download url for file.
    """
    client = get_box_client()
    return client.file(file_id).get_download_url()


def get_preview_url(file_id):
    """
    Generate preview url.
    """
    client = get_box_client()
    return client.file(file_id).get_shared_link_download_url(
        access='open',
        allow_preview=True)

def get_document(document_type, client_dba, client_license, document_id):
    """
    Get estimate, SO, PO, Invoices from box.
    """
    if document_type.lower() in ['estimates', 'sales_orders', 'purchase_orders', 'invoices']:
        dir_name = f'{client_dba}_{client_license}'
        folder_id = get_client_folder_id(dir_name)
        sub_folder_id = search(folder_id, document_type)
        sub_folder_content = get_folder_items(sub_folder_id)
        for k,v in sub_folder_content.items():
            if v.split('.')[0] == document_id:
                return get_preview_url(k)
    return {
        'status_code': 1,
        'error': 'No document or folder found.'
    }

def get_thumbnail_url(file_id, folder_id, file_name):
    """
    Get thumbnail url.
    """
    client = get_box_client()
    data = BytesIO(client.file(file_id).get_thumbnail(
        extension='jpg',
        min_width=50, min_height=50))
    file_name = file_name.split('.')
    file_name = file_name[0] + '-thumbnail.' + file_name[1]
    thumbnail_id = upload_file_stream(folder_id, data, file_name)
    try:
        return get_preview_url(thumbnail_id.id)
    except AttributeError:
        return get_preview_url(thumbnail_id)

def get_file_from_link(link):
    """
    Return file information using shared link.
    """
    client = get_box_client()
    return client.get_shared_item(link)

def rename_file(file_id, new_name):
    """
    Rename file.
    """
    client = get_box_client()
    file_to_rename = client.file(file_id)
    renamed_file = file_to_rename.rename(new_name)
    return renamed_file
