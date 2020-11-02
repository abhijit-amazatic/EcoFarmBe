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
from core.celery import app
from integration.crm import (get_records_from_crm,get_accounts_from_crm,)
from brand.models import *

slack = Slacker(settings.SLACK_TOKEN)

BS = 16
key = hashlib.md5(str('asdsadsadsds').encode('utf-8')).hexdigest()[:BS]

NOUN_PROCESS_MAP = {"cultivator":"cultivation","nursery":"nursery","manufacturer":"manufacturing",
                    "distributor":"distribution","retailer":"retail","processor":"processing",
                    "testing":"testing","event":"event","brand":"brand","hemp":"hemp",
                    "ancillary products":"ancillary products","ancillary services":"ancillary services",
                    "investor":"investment","patient":"patient","healthcare":"healthcare"}

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
    slack.chat.post_message(settings.SLACK_CHANNEL_NAME,msg, as_user=True)
    #mail_send("notify.html",{'link': email},"New Profile User registration.", recipient_list=settings.ADMIN_EMAIL)


def notify_admins_on_profile_registration(email,farm):
    """
    Notify admins on slack & email about new farm registration under farm.
    """
    msg = "<!channel>New Vendor/Account profile is registered with us with the Profile name as  - %s under the EmailID `%s`.Please review and approve from admin Panel!" % (farm, email)
    slack.chat.post_message(settings.SLACK_CHANNEL_NAME,msg, as_user=True)
    mail_send("farm-register.html",{'link': farm,'mail':email},"Profile registration.", recipient_list=settings.ADMIN_EMAIL)
    
    
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
    
@app.task(queue="general")
def add_users_to_system_and_license(profile_contact_id,license_obj_id):
    """
    ->create users into system(if not exist)+add then unser licese,
    ->notify admins(email& slack) about new user addition,
    ->send newly addd users a verification link
    ->send email to set password, 
    """
    role_map = {"License Owner":"license_owner","Farm Manager":"farm_manager","Sales/Inventory":"sales_or_inventory","Logistics":"logistics","Billing":"billing","Owner":"owner"}
    
    pro_contact_obj = ProfileContact.objects.filter(id=profile_contact_id)
    license_obj = License.objects.filter(id=license_obj_id)
    if pro_contact_obj:
        employee_data = pro_contact_obj[0].profile_contact_details.get('employees')
        extracted_employee = [i for i in employee_data if i.get('employee_email')]      
        for employee in extracted_employee:
            obj, created = User.objects.get_or_create(email=employee['employee_email'],
                                                      defaults={'email':employee['employee_email'],
                                                                'username':employee['employee_name'],
                                                                'phone':employee['phone'],
                                                                'is_verified':False,
                                                                'membership_type':"personal",
                                                                'existing_member':True})
            
            if not LicenseUser.objects.filter(user_id=obj.id,license_id=license_obj_id).exists():
                extracted_role = role_map.get(employee['roles'][0])
                LicenseUser(user_id=obj.id,license_id=license_obj_id,role=extracted_role).save()
                notify_admins_on_profile_user_registration(obj.email,license_obj[0].license_profile.name)
                link = get_encrypted_data(obj.email,reason='verify')
                mail_send("verification-send.html",{'link': link},"Thrive Society Verification.",obj.email)
                notify_profile_user(obj.email,license_obj[0].license_profile.name)
                    
                                
@app.task(queue="general")
def send_async_approval_mail(profile_id):
    """
    Async email send for after profile approval.
    """
    license_obj = License.objects.filter(id=profile_id)
    if license_obj:
        ac_manager = license_obj[0].created_by.email
        mail_send("farm-approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login'},"Profile Approved.", ac_manager)

        
@app.task(queue="general")        
def send_async_user_approval_mail(user_id):
    """
    Async email send for after user approval.
    """
    user = User.objects.filter(id=user_id)    
    mail_send("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login'},"Account Approved.", user[0].email)

    
def send_verification_link(email):
    """
    Send verification link to user.
    """
    link = get_encrypted_data(email,reason='verify')
    mail_send("verification-send.html",{'link': link},"Thrive Society Verification.",email)


def create_license(user,profile_type,data):
    """
    create for accounts/vendors based on condition
    """
    #category = [v for k,v in NOUN_PROCESS_MAP.items() if v.lower() == account.lower()]
    License.objects.bulk_create([License(created_by=user,
                                         license_type=key.get('license_type',''),
                                         owner_or_manager='Owner' if key.get('Owner') else 'Manager',
                                         legal_business_name=key.get('legal_business_name',''),
                                         license_number=key.get('license_number',''),
                                         expiration_date=key.get('expiration_date',''),
                                         issue_date=key.get('issue_date',''),
                                         premises_address=key.get('premises_address',''),
                                         premises_county=key.get('premises_county',''),
                                         premises_city = key.get('premises_city',''),
                                         zip_code=key.get('zip_code',''),
                                         premises_apn=key.get('premises_apn',''),
                                         premises_state=key.get('premises_state',''),
                                         uploaded_sellers_permit_to=key.get('uploaded_sellers_permit_to',''),
                                         uploaded_w9_to=key.get('uploaded_w9_to',''),                               
                                         uploaded_license_to=key.get('uploaded_license_to',''),
                                         is_seller=True if profile_type=='seller' else False,
                                         is_buyer=True if profile_type =='buyer' else False,
                                         profile_category=data.get('vendor_type')[0].lower() if len(data.get('vendor_type')) and profile_type == 'seller' else None) for key in data.get('licenses')], ignore_conflicts=False)
    
    
def insert_data_from_crm(user,profile_category,data,profile_type):
    """
    Insert available data from crm to database.
    """
    if profile_type == "seller":
        with transaction.atomic():
            #STEP 1:License create
            if data.get('licenses'):
                create_license(user,'seller', data)
    elif profile_type == "buyer":
        with transaction.atomic():
            create_license(user,'buyer', data)
        
        
        
        
    
    
@app.task(queue="general")
def get_from_crm_insert_to_vendor_or_account(user_id):
    """
    async task for existing user.
    """
    instance = User.objects.filter(id=user_id)
    if instance:
        if instance[0].legal_business_name:
            for business in instance[0].legal_business_name:
                vendors_data = get_records_from_crm(business)
                if not vendors_data.get('error'):
                    insert_data_from_crm(instance[0],vendors_data.get('vendor_type'), vendors_data,'seller')
                accounts_data = get_accounts_from_crm(business)
                if not accounts_data.get('error'):
                    insert_data_from_crm(instance[0],accounts_data.get('basic_profile',{}).get('company_type'), accounts_data,'buyer')


    


