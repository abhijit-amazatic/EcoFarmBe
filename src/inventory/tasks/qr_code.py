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
from integration.box import delete_file

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
        payload.update({'size':100})
        
    response = request("POST", rapid_url, headers=headers, data=json.dumps(payload))
    img = BytesIO(response.content)
    try:
        new_file=upload_file_stream(settings.INVENTORY_QR_UPLOAD_FOLDER_ID,img,"%s.png"%item)
        box_url= get_preview_url(new_file.id)
    except AttributeError:
        print("Exception.File already exists.")
        box_url= get_preview_url(new_file)
    try:
        obj = InventoryModel.objects.get(item_id=item)
        obj.item_qr_code_url = box_url
        obj.save()
        print("Generated/Uploaded/Saved QR code URL of item '%s' is '%s'.\n" %(item,box_url))
    except InventoryModel.DoesNotExist as e:
        print("Item is not in databse.\n Box URL is", box_url)
        return box_url
    

def update_inventory_qr_codes():
    """
    Update  inventory QR urls for existing items.
    """
    inventory = InventoryModel.objects.filter(status='active',cf_cfi_published=True)
    for item in inventory:
        if not item.item_qr_code_url:
            generate_upload_item_detail_qr_code_stream.delay(item.item_id)
    
        
    

