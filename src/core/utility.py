"""
Generic functions needed.
"""

import hashlib
import base64
from django.conf import settings
from Crypto.Cipher import AES
from Crypto import Random
from django.contrib.auth.password_validation import validate_password as default_validate_password
from core.mailer import mail, mail_send
from slacker import Slacker
from django.db import transaction
from user.models import *
from vendor.models import *

slack = Slacker(settings.SLACK_TOKEN)

BS = 16
key = hashlib.md5(str('asdsadsadsds').encode('utf-8')).hexdigest()[:BS]


def pad(s):
    """
    to adding padding in string for encryption purpose
    """
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)


def unpad(s):
    """
    to remove padding in string for decryption purpose
    """
    return s[:-ord(s[len(s) - 1:])]


def get_encrypted_data(email, reason=None):
        raw = pad(email)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = base64.urlsafe_b64encode(iv + cipher.encrypt(raw))
        if reason == "forgot_password" or "reset_user_password":
            return '{}reset-password?code={}'.format(settings.FRONTEND_DOMAIN_NAME, cipher_text.decode('ascii'))
        else:
           return '{}verify-user?code={}'.format(settings.FRONTEND_DOMAIN_NAME, cipher_text.decode('ascii'))

def get_decrypted_data(enc):
        enc = base64.urlsafe_b64decode(enc)
        iv = enc[:BS]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc[BS:]))       


def notify_admins_on_vendors_registration(email,farm):
    """
    Notify admins on slack & email about new user registration under farm.
    """
    msg = "<!channel>User with the EmailID `%s`  is registered with us for the farm - %s.Please review and approve from admin Panel!" % (email, farm)
    slack.chat.post_message(settings.SLACK_CHANNEL_NAME,msg, as_user=True)
    mail_send("notify.html",{'link': email},"New Farm User registration.", recipient_list=settings.ADMIN_EMAIL)


def notify_admins_on_profile_registration(email,farm):
    """
    Notify admins on slack & email about new farm registration under farm.
    """
    msg = "<!channel>New Vendor profile is registered with us with the farm name as  - %s under the EmailID `%s`.Please review and approve from admin Panel!" % (farm, email)
    slack.chat.post_message(settings.SLACK_CHANNEL_NAME,msg, as_user=True)
    mail_send("farm-register.html",{'link': farm,'mail':email},"Vendor Profile registration.", recipient_list=settings.ADMIN_EMAIL)
    

def notify_farm_user(recipient_email,farm):
    """
     Notify farm user.
     """
    link = get_encrypted_data(recipient_email, 'reset_user_password')
    subject = "Set Password for your profile with Eco-Farm."
    mail_send(
        "farm-notify.html",
        {
            # 'first_name': recipient_email.capitalize(),
            'link': link,
            'farm':farm
        }, subject, recipient_email
    )   
    

def insert_data_for_vendor_profile(user,vendor_type,data):
    """
    For existing user, to insert records to perticular vendor profile use this function.
    In order to store data of existing user from crm to our db few things needs to be 
    1.For existing user we need to create vendors as well as vendor profile for given vendor type e. cultivator
    2.parameter could be vendor_type = ['cultivator','nursary']
    3.data will be dict of multiple model fields
    """
    
    #get exsiting given category with user and for e.g 'cultivator' if added in vendor_type list.
    #whenever you create vendor we must add entry of that in vendor user
    for vendor in vendor_type:
        obj,created = Vendor.objects.get_or_create(ac_manager=user,vendor_category=vendor)
        if not VendorUser.objects.filter(user=user, vendor=obj.id).exists():
            VendorUser.objects.create(user=user, vendor_id=obj.id,role='Owner')
            
        vendor_user=VendorUser.objects.get(user=user,vendor=obj)
        if vendor_user.role == 'Owner' and user.existing_member:
            """
            Only first owner can pull & store data as others will have access anyways.(This will be first owner as profileusers 
            are added with another role aling with this if added user is owner)
            """
            vp, created = VendorProfile.objects.get_or_create(vendor=obj) #for step1 create vendor profile
            with transaction.atomic():
                #STEP1 - update respected data if you want to else comment this
                vp_step1 = VendorProfile(number_of_licenses=data.get('vendor_profile')['number_of_licenses'],
                                         number_of_legal_entities=data.get('vendor_profile')['number_of_legal_entities'],
                                         vendor=vp)
                vp_step1.save()

                #Step1 - add license data else comment this,add more fieldshere.I've addded only one field to create
                lc_step1  = License(license_type = data.get('license')['license_type'], vendor_profile=vp)
                lc_step1.save()
                
                #STEP2-add profile contact data
                pc_step2 = ProfileContact(vendor_profile=vp, is_draft="false",profile_contact_details = data.get('profile_contact'))
                pc_step2.save()

                #STEP3 - add profile_overview

                po_step3 = ProfileOverview(vendor_profile=vp, is_draft="false", profile_overview=data.get(' profile_overview'))
                po_step3.save()

                #STEP4 - add  processing_config
                pc_step4 = ProcessingOverview(vendor_profile=vp, is_draft="false", processing_config=data.get('processing_config'))
                pc_step4.save()

                #STEP5 - add financial details
                fd_step5 = FinancialOverview(vendor_profile=vp,is_draft="false", financial_details=data.get('financial_details'))
                fd_step5.save()
                
                #STEP6 - add program overview
                po_step6 = ProgramOverview(vendor_profile=vp,is_draft="false",program_details=data.get('program_details'))
                po_step6.save()

                
                

    
    
