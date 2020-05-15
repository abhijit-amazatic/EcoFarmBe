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
from core.celery import app
from integration.crm import (get_records_from_crm,)

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
    
@app.task(queue="general")
def add_users_to_system(profile_contact_id,vendor_profile_id,vendor_obj_id):
    """
    Create users in system from profile contact.
    Add them to vendors.
    Invite them to change password.(if users not exists already)
    """
    pro_contact_obj = ProfileContact.objects.filter(id=profile_contact_id)
    if pro_contact_obj:
        employee_data = pro_contact_obj[0].profile_contact_details.get('employees')
              
        for employee in employee_data:
            obj, created = User.objects.get_or_create(email=employee['employee_email'],
                                                      defaults={'email':employee['employee_email'],
                                                                'username':employee['employee_name'],
                                                                'phone':employee['phone'],
                                                                'is_verified':True,
                                                                'existing_member':True})
            if created:
                if not VendorUser.objects.filter(user_id=obj.id, vendor_id=vendor_obj_id).exists():
                    VendorUser(user_id=obj.id, vendor_id=vendor_obj_id,role=','.join(employee['roles'])).save()
                    notify_farm_user(obj.email, pro_contact_obj[0].profile_contact_details.get('farm_name'))
                    notify_admins_on_vendors_registration(obj.email,pro_contact_obj[0].profile_contact_details.get('farm_name'))
                    
                        
@app.task(queue="general")
def insert_data_for_vendor_profile(user,vendor_type,data):
    """
    For existing user, to insert records to perticular vendor profile use this function.
    In order to store data of existing user from crm to our db few things needs to be 
    1.For existing user we need to create vendors as well as vendor profile for given vendor type e. cultivator
    2.parameter could be vendor_type = ['cultivation','nursary']
    3.data will be dict of multiple model fields
    """
    try:
        for vendor in vendor_type:
            obj,created = Vendor.objects.get_or_create(ac_manager=user,vendor_category=NOUN_PROCESS_MAP.get(vendor))
            if not VendorUser.objects.filter(user_id=user.id, vendor=obj.id).exists():
                VendorUser.objects.create(user_id=user.id, vendor_id=obj.id,role='Owner')         
            vendor_user=VendorUser.objects.get(user_id=user.id,vendor=obj)
            if vendor_user.role == 'Owner' and user.existing_member and vendor == "cultivation":
                """
                Only first owner can pull & store data as others will have access anyways.(This will be first owner as profileusers 
                are added with another role aling with this if added user is owner)
                """
                vp, created = VendorProfile.objects.get_or_create(vendor=obj) #for step1 create vendor profile
                print('vendor_profile to be updated->', vp)
                with transaction.atomic():
                    #STEP1
                    if data.get('licenses'):
                        License.objects.bulk_create([License(vendor_profile_id=vp.id,
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
                                                             uploaded_license_to=key.get('uploaded_license_to','')) for key in data.get('licenses')], ignore_conflicts=False)
                        print("STEP1 License fetched in DB")
                with transaction.atomic():     
                    #STEP2-add profile contact data
                    contacts = list(data.get('profile_contact').get('employees').keys())
                    formatted_data = {"farm_name":data.get('profile_contact').get('farm_name',''),
                                      "primary_county":data.get('profile_contact').get('primary_county',''),
                                      "region":data.get('profile_contact').get('region',''),
                                      "appellation":data.get('profile_contact').get('appellation',''),
                                      "ethics_and_certifications":data.get('profile_contact').get('ethics_and_certifications',[]),
                                      "other_distributors":data.get('profile_contact').get('other_distributors',''),
                                      "transportation":data.get('profile_contact').get('transportation',[]),
                                      "packaged_flower_line":data.get('profile_contact').get('packaged_flower_line',''),
                                      "interested_in_co_branding":data.get('profile_contact').get('interested_in_co_branding',''),
                                      "marketing_material":data.get('profile_contact').get('marketing_material',''),
                                      "featured_on_our_site":data.get('profile_contact').get('featured_on_our_site',''),
                                      "company_email":data.get('profile_contact').get('company_email',''),
                                      "company_phone":data.get('profile_contact').get('company_phone',''),
                                      "website":data.get('profile_contact').get('website',''),
                                      "instagram":data.get('profile_contact').get('instagram',''),
                                      "facebook":data.get('profile_contact').get('facebook',''),
                                      "linkedin":data.get('profile_contact').get('linkedin',''),
                                      "twitter":data.get('profile_contact').get('twitter',''),
                                      "no_of_employees":data.get('profile_contact').get('no_of_employees',''),
                                      "employees":[{"employee_name":data.get('profile_contact').get('employees').get('Cultivation Manager','')['employee_name'],
                                                    "employee_email":data.get('profile_contact').get('employees').get('Cultivation Manager','')['employee_email'] ,
                                                    "phone":data.get('profile_contact').get('employees').get('Cultivation Manager','')['phone'],
                                                    "roles":[contact]} for contact in contacts]}
                    pc_step2, created = ProfileContact.objects.get_or_create(vendor_profile_id=vp.id, is_draft=False,profile_contact_details = formatted_data)
                    if created:
                        add_users_to_system.delay(pc_step2.id,vp.id,obj.id)
                    print("STEP2 Profile contact fetched in DB")
                with transaction.atomic():
                    profile_data = {"lighting_type":data.get('profile_overview').get('lighting_type',[]),
                                    "type_of_nutrients":data.get('profile_overview').get('type_of_nutrients,'''),
                                    "interested_in_growing_genetics":data.get('profile_overview').get('interested_in_growing_genetics'),
                                    "issues_with_failed_lab_tests":data.get('profile_overview').get('issues_with_failed_lab_tests'),
                                    "lab_test_issues":data.get('profile_overview').get('lab_test_issues'),
                                    "plants_cultivate_per_cycle":data.get('profile_overview').get('plants_cultivate_per_cycle',0),
                                    "annual_untrimmed_yield":data.get('profile_overview').get('annual_untrimmed_yield',0),
                                    "no_of_harvest":data.get('profile_overview').get('no_of_harvest',0),
                                    "indoor_sqf":data.get('profile_overview').get('indoor_sqf',0),
                                    "outdoor_sqf":data.get('profile_overview').get('outdoor_sqf',0),
                                    "mixed_light_no_of_harvest":data.get('profile_overview').get('mixed_light_no_of_harvest',0),
                                    "indoor_no_of_harvest":data.get('profile_overview').get('indoor_no_of_harvest',0),
                                    "outdoor_no_of_harvest":data.get('profile_overview').get('outdoor_no_of_harvest',0),
                                    "mixed_light_sqf":data.get('profile_overview').get('mixed_light_sqf',0)} 
                    #STEP3 - add profile_overview
                    po_step3 = ProfileOverview.objects.get_or_create(vendor_profile_id=vp.id, is_draft=False, profile_overview=profile_data)
                    print("STEP3 Profile Overview fetched in DB")
                with transaction.atomic():         
                    #STEP4 - add  processing_config
                    harvest_dates = [value for key, value in data.get('processing_config').items() if 'harvest_' in key.lower()]
                    cultivars_data = data.get('processing_config').get('cultivars','')
                    if cultivars_data:
                        cultivars = cultivars_data.split(',')
                    else:
                        cultivars = ""
                    processing_data = {"flower_yield_percentage": data.get('processing_config').get('flower_yield_percentage',0),
		                       "small_yield_percentage": data.get('processing_config').get('small_yield_percentage',0),
		                       "trim_yield_percentage": data.get('processing_config').get('trim_yield_percentage',0),
		                       "know_yield_per_plant":data.get('processing_config').get('know_yield_per_plant',''),
		                       "yield_per_plant":data.get('processing_config').get('yield_per_plant',0),
		                       "know_yield_per_sq_ft":data.get('processing_config').get('know_yield_per_sq_ft',''),
		                       "avg_yield_pr_sq_ft":data.get('processing_config').get('avg_yield_pr_sq_ft',0),
                                       "cultivars": [{"harvest_date":date, "cultivar_names": cultivars } for date in harvest_dates]}
                    pc_step4 = ProcessingOverview.objects.get_or_create(vendor_profile_id=vp.id, is_draft=False, processing_config=data.get('processing_config'))
                    print("STEP4 Proc.Overview fetched in DB")
                with transaction.atomic():   
                    #STEP5 - add financial details
                    fd_step5 = FinancialOverview.objects.get_or_create(vendor_profile_id=vp.id,is_draft=False, financial_details=data.get('financial_details'))
                    print("STEP5 Financial data fetched in DB") 
    except Exception as e:
        print('Exception\n',e)

                
@app.task(queue="general")
def get_from_crm_insert_to_vendorprofile(user_id):
    """
    async task for existing user.
    """
    instance = User.objects.filter(id=user_id)
    if instance:
        crm_data = get_records_from_crm(instance[0].legal_business_name)
        if crm_data:
            insert_data_for_vendor_profile(instance[0],crm_data.get('vendor_type'), crm_data)
    
        
@app.task(queue="general")
def send_async_approval_mail(profile_id):
    """
    Async email send for after profile approval.
    """
    vendor_obj = Vendor.objects.filter(id=profile_id)
    if vendor_obj:
        ac_manager = vendor_obj[0].ac_manager.email
        mail_send("farm-approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login'},"Profile Approved.", ac_manager)
