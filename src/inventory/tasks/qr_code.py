"""
QR code related tasks
"""
import os
import json
from io import (BytesIO, BufferedReader)
from requests import  request
from django.conf import settings
from django.utils import timezone
from core.celery import (app,)
from celery.task import periodic_task
from celery.schedules import crontab
from integration.box import (upload_file_stream, upload_file,get_preview_url,)
import base64
from PIL import Image
from boxsdk.exception import (BoxOAuthException,
                              BoxException, BoxAPIException)
from inventory.models import Inventory as InventoryModel
from integration.box import (delete_file,search,rename_file)

@app.task(queue="general")
def generate_upload_item_detail_qr_code_stream(item,size=None):
    """
    QR code generate for item_id & upload to box.
    Note: 
    -If new file uploaded using stream box use 'id' to access preview url as it returns object.
    -If file already exists, box returns id of type string use that to get preview url.
    """
    rapid_url = "https://qrcode-monkey.p.rapidapi.com/qr/custom"
    headers = {
        'Content-Type': 'application/json',
        'x-rapidapi-host': 'qrcode-monkey.p.rapidapi.com',
        'x-rapidapi-key': settings.RAPID_API_KEY
    }
    payload ={
        'data': settings.FRONTEND_DOMAIN_NAME+"marketplace/"+str(item)+"/item",
        'config': {'bodyColor': '#013C48', 'bgColor': '#FFFFFF', 'gradientOnEyes': False, 'logo': '5077de589ef4588913df60364d47fedc6347f431.png', 'body': 'rounded-pointed', 'eye': 'frame14', 'eyeBall': 'ball16', 'erf1': [], 'erf2': ['fh'], 'erf3': ['fv'], 'brf1': [], 'brf2': ['fh'], 'brf3': ['fv'], 'eye1Color': '#1a6160', 'eye2Color': '#1a6160', 'eye3Color': '#1a6160', 'eyeBall1Color': '#1a6160', 'eyeBall2Color': '#1a6160', 'eyeBall3Color': '#1a6160', 'gradientColor1': '#1a6160', 'gradientColor2': '#1a6160', 'gradientType': 'radial'},
        'download': False,
        'file': 'png'}
    if size:
        payload.update({'size':size})
    else:
        payload.update({'size':200})
        
    response = request("POST", rapid_url, headers=headers, data=json.dumps(payload))
    img = BytesIO(response.content)
    try:
        obj = InventoryModel.objects.get(item_id=item)
        new_file=upload_file_stream(settings.INVENTORY_QR_UPLOAD_FOLDER_ID,img,"%s.png"%obj.sku.strip())
        box_url= get_preview_url(new_file.id)
        box_file_id=new_file.id
    except BoxAPIException as e:
        print('Item name is not valid', e)
        new_file=upload_file_stream(settings.INVENTORY_QR_UPLOAD_FOLDER_ID,img,"%s.png"%item)
        box_url= get_preview_url(new_file.id)
        box_file_id=new_file.id
    except AttributeError:
        print("Exception.File already exists.")
        box_url= get_preview_url(new_file)
        box_file_id=search(settings.INVENTORY_QR_UPLOAD_FOLDER_ID,"%s.png"%obj.sku.strip())        
    obj.item_qr_code_url = box_url
    obj.qr_code_box_id = box_file_id
    obj.qr_box_direct_url = "https://ecofarm.app.box.com/file/"+str(box_file_id)
    obj.save()
    print("Generated/Uploaded/Saved QR code URL of item '%s'with sku '%s' is '%s'.\n" %(item,obj.sku,box_url))


def update_inventory_qr_codes():
    """
    Update  inventory QR urls for existing items.
    """
    inventory = InventoryModel.objects.filter(status='active',cf_cfi_published=True)
    for item in inventory:
        generate_upload_item_detail_qr_code_stream.delay(item.item_id)
    
        
def remove_all_existing_qr_codes_from_box():
    """
    Remove existing QR codes & update db links to None
    """
    inventory = InventoryModel.objects.filter(status='active',cf_cfi_published=True)
    for obj in inventory:
        box_obj_id = search(settings.INVENTORY_QR_UPLOAD_FOLDER_ID,"%s.png"%obj.sku.strip())
        if box_obj_id:
            delete_file(box_obj_id)
            obj.item_qr_code_url=None
            obj.save()
            print('Removed/Updated link for', obj.item_id)
            
            
def rename_all_existing_qr_codes_from_box():
    """
    Rename existing QR codes to sku form item_id.
    """
    inventory = InventoryModel.objects.filter(status='active',cf_cfi_published=True,qr_code_box_id__isnull=False)
    for obj in inventory:
        try:
            rename_file.delay(obj.qr_code_box_id,'%s.png'%obj.sku.strip())
        except Exception as e:
            print('Exception while renaming', obj.item_id)
            
