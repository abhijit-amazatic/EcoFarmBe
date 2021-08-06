"""
Generic functions needed.
"""

import hashlib
import base64
import re
import json
from django.conf import settings
from Crypto.Cipher import AES
from Crypto import Random
from django.contrib.auth.password_validation import validate_password as default_validate_password
from core.mailer import mail, mail_send
from slacker import Slacker
from django.db import transaction
from user.models import *
from core.celery import app
from brand.models import *
from utils import (reverse_admin_change_path,)


slack = Slacker(settings.SLACK_TOKEN)

BS = 16
key = hashlib.md5(str('asdsadsadsds').encode('utf-8')).hexdigest()[:BS]

NOUN_PROCESS_MAP = {"cultivator":"cultivation","nursery":"nursery","manufacturer":"manufacturing",
                    "distributor":"distribution","retailer":"retail","processor":"processing",
                    "testing":"testing","event":"event","brand":"brand","hemp":"hemp",
                    "ancillary products":"ancillary products","ancillary services":"ancillary services",
                    "investor":"investment","patient":"patient","healthcare":"healthcare"}


def get_key(val):
    """
    function to return key for any value.
    """ 
    for key, value in NOUN_PROCESS_MAP.items(): 
         if val == value: 
             return key 
  
    return "farm"

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


def get_encrypted_data(email,reason=None):
        raw = pad(email)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(bytes(key,'utf-8'),AES.MODE_CBC,iv)
        cipher_text = base64.urlsafe_b64encode(iv + cipher.encrypt(bytes(raw,'utf-8')))
        if reason == "verify":
            return '{}verify-user?code={}'.format(settings.FRONTEND_DOMAIN_NAME, cipher_text.decode('ascii'))
        elif reason == "forgot_password" or "reset_user_password":
            return '{}reset-password?code={}'.format(settings.FRONTEND_DOMAIN_NAME, cipher_text.decode('ascii'))
        
            
        
def get_decrypted_data(enc):
        enc = base64.urlsafe_b64decode(enc)
        iv = enc[:BS]
        cipher = AES.new(bytes(key,'utf-8'),AES.MODE_CBC,iv)
        return unpad(cipher.decrypt(enc[BS:]))       


def notify_admins_on_profile_user_registration(email,profile):
    """
    Notify admins on slack & email about new user registration under profile.
    """
    msg = "<!channel>User with the EmailID `%s` is registered with us for the profile-%s" % (email, farm)
    slack.chat.post_message(settings.SLACK_CHANNEL_NAME,msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)
    #mail_send("notify.html",{'link': email},"New Profile User registration.", recipient_list=settings.ADMIN_EMAIL)


def email_admins_on_profile_registration_completed(email,farm,instance,admin_link):
    """
    Notify admins on email about new farm registration under farm.when status is 'Completed'
    """
    mail_send("farm-register.html",{'farm_name': farm,'mail':email,'admin_link': admin_link,'license_type':instance.license_type,'legal_business_name':instance.legal_business_name,'license_number':instance.license_number },"License Profile [%s] registration completed." % instance.license_number, recipient_list=settings.ONBOARDING_ADMIN_EMAIL)

def email_admins_on_profile_progress(user,instance,admin_link):
    """
    Notify admins on email about new profile in progress.
    """
    mail_send("farm-progress.html",{'admin_link': admin_link,'mail':user.email,'license_type':instance.license_type,'legal_business_name':instance.legal_business_name,'license_number':instance.license_number},"License Profile [%s] is created & in progress." % instance.license_number, recipient_list=settings.ONBOARDING_ADMIN_EMAIL)    
    
def notify_admins_on_slack(email,license_instance,admin_link):
    """
    as license onboarded, inform admin on slack.
    """
    msg = "<!channel>New License is registered with us (step 1) under the organization  - *%s*, associated with the EmailID `%s`.Please review/check whether they need any assistance!\n- *Legal Business name:* %s\n- *Profile Category:* %s\n- *License Number:* %s\n - *County:* %s\n- *Admin Link:* %s\n" % (license_instance.organization.name, email, license_instance.legal_business_name,license_instance.profile_category,license_instance.license_number,license_instance.premises_county,admin_link)
    slack.chat.post_message(settings.SLACK_ONBOARDING_PROGRESS,msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)

def notify_admins_on_slack_complete(email,instance,admin_link):
    """
    as license onboarded 'completed', inform admin on slack.
    """
    msg = "<!channel>New License profile was 'Completed' under the organization - *%s*, associated with the EmailID `%s`.Please mark it's status as 'Approved' from the admin panel after license & profile have been verified for compliance and accuracy!\n- *Legal Business name:* %s\n- *Profile Category:* %s\n- *License Number:* %s\n - *County:* %s\n- *Admin Link:* %s\n" % (instance.organization.name, email, instance.legal_business_name,instance.profile_category,instance.license_number,instance.premises_county,admin_link)
    try:
        channel_dict = json.loads(settings.SLACK_ONBOARDING_COMPLETED)
    except Exception as e:
        channel_dict = settings.SLACK_ONBOARDING_COMPLETED   
    slack.chat.post_message(channel_dict.get(instance.profile_category,'tech_dev_slack_testing'),msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)    
    
def notify_profile_user(recipient_email,farm):
    """
     Notify farm/profile user.
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


# def extract_all_roles_from_email(email,data):
#     """
#     Extract all roles if same email for existing user.
#     """
#     final_roles = []
#     for i in data:
#         if i.get('employee_email') == email:            
#             final_roles.extend(i.get('roles'))
#     return final_roles
    
# @app.task(queue="general")
# def add_users_to_system_and_license(profile_contact_id,license_obj_id):
#     """
#     ->create users into system(if not exist)+add then unser licese,
#     ->notify admins(email& slack) about new user addition,
#     ->send newly addd users a verification link
#     ->send email to set password, 
#     """
#     role_map = {"License Owner":"license_owner","Farm Manager":"farm_manager","Sales/Inventory":"sales_or_inventory","Logistics":"logistics","Billing":"billing","Owner":"owner"}
#     #updated_role_map  =  {"Cultivation Manager":"farm_manager","Sales Manager":"sales_or_inventory","Logistics Manager":"logistics","Billing / Accounting":"billing","Owner":"owner"}
    
#     pro_contact_obj = ProfileContact.objects.filter(id=profile_contact_id)
#     license_obj = License.objects.filter(id=license_obj_id)
#     if pro_contact_obj:
#         employee_data = pro_contact_obj[0].profile_contact_details.get('employees')
#         extracted_employee = [i for i in employee_data if i.get('employee_email')]      
#         for employee in extracted_employee:
#             obj, created = User.objects.get_or_create(email=employee['employee_email'],
#                                                       defaults={'email':employee['employee_email'],
#                                                                 'username':employee['employee_name'],
#                                                                 'phone':employee['phone'],
#                                                                 'is_verified':False,
#                                                                 'membership_type':"personal",
#                                                                 'existing_member':True})
            
#             if not LicenseUser.objects.filter(user_id=obj.id,license_id=license_obj_id).exists():
#                 try:
#                     all_roles = list(set(extract_all_roles_from_email(employee['employee_email'],employee_data)))
#                     extracted_role = [role_map.get(i) for i in all_roles] #role_map.get(employee['roles'])
#                     role_ids = LicenseRole.objects.filter(name__in=extracted_role).values_list(flat=True)
#                     license_user = LicenseUser.objects.create(user_id=obj.id,license_id=license_obj_id)
#                     license_user.role.set(list(role_ids))
#                     license_user.save()
#                     notify_admins_on_profile_user_registration(obj.email,license_obj[0].license_profile.name)
#                     link = get_encrypted_data(obj.email,reason='verify')
#                     mail_send("verification-send.html",{'link': link},"Thrive Society Verification.",obj.email)
#                     notify_profile_user(obj.email,license_obj[0].license_profile.name)
#                 except Exception as e:
#                     print("Exception while adding license user",e)
                    


def get_profile_type(obj):
    """
    return buyer or seller based on condition.
    #return 'Buyer' if obj.is_buyer else 'Seller'
    """
    return get_key(obj.profile_category).capitalize()
    
@app.task(queue="general")
def send_async_approval_mail(profile_id):
    """
    Async email send for after profile approval.'profile_id'is actually license obj id
    """
    license_obj = License.objects.filter(id=profile_id)
    if license_obj:
        ac_manager = license_obj[0].organization.created_by.email
        profile_type = get_profile_type(license_obj[0])
        mail_send("farm-approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login','profile_type': profile_type,'legal_business_name': license_obj[0].legal_business_name},"Your %s profile has been approved."% profile_type, ac_manager)

@app.task(queue="general")
def send_async_approval_mail_admin(obj_id,req_user_id):
    """
    Async email send to admin after profile approval.
    """
    license_obj = License.objects.filter(id=obj_id)
    user = User.objects.get(id=req_user_id)
    if license_obj:
        admin_link = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(license_obj[0])}"
        mail_send("farm-approved-admin.html",{'admin_link': admin_link,'mail':user.email,'license_type':license_obj[0].license_type,'legal_business_name':license_obj[0].legal_business_name,'license_number':license_obj[0].license_number},"License Profile [%s] approved" % license_obj[0].license_number, recipient_list=settings.ONBOARDING_ADMIN_EMAIL)

        
@app.task(queue="general")        
def send_async_user_approval_mail(user_id):
    """
    Async email send for after user approval.
    """
    user = User.objects.filter(id=user_id)    
    mail_send("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login','full_name': user[0].full_name},"Account Approved.", user[0].email)
        
def send_verification_link(email):
    """
    Send verification link to user.
    """
    user = User.objects.filter(email=email)
    link = get_encrypted_data(email,reason='verify')
    mail_send("verification-send.html",{'link': link,'full_name': user[0].full_name},"Thrive Society Verification.",email)

def send_verification_link_user_instance(user):
    """
    Send verification link to user.
    """
    link = get_encrypted_data(user.email,reason='verify')
    mail_send("verification-send.html",{'link': link,'full_name': user.full_name},"Thrive Society Verification.",user.email)
