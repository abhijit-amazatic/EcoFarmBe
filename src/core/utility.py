"""
Generic functions needed.
"""

import hashlib
import base64
import re
from django.conf import settings
from Crypto.Cipher import AES
from Crypto import Random
from django.contrib.auth.password_validation import validate_password as default_validate_password
from core.mailer import mail, mail_send
from slacker import Slacker
from django.db import transaction
from user.models import *
from core.celery import app
from integration.crm import (get_records_from_crm,)
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
                    


def get_profile_type(obj):
    """
    return buyer or seller based on condition.
    """
    return 'Buyer' if obj.is_buyer else 'Seller'
    
    
@app.task(queue="general")
def send_async_approval_mail(profile_id):
    """
    Async email send for after profile approval.
    """
    license_obj = License.objects.filter(id=profile_id)
    if license_obj:
        ac_manager = license_obj[0].created_by.email
        profile_type = get_profile_type(license_obj[0])
        mail_send("farm-approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login','profile_type': profile_type},"Profile Approved.", ac_manager)

        
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


def get_employee(data):
    """
    structure employee according to db format & insert empty data also.(currently insefrted empty contacts)
    """
    final_data = []
    final_contacts = ["License Owner","Farm Manager","Logistics","Sales/Inventory","Billing"]

    for i in final_contacts:
        final_data.append({"employee_name":"",
                           "employee_email":"",
                           "phone":"",
                           "roles":[i]})
    return final_data 

def get_crop_overview(license_data,data):
    """
    Format crop overview.
    """
    return [{'cultivars':[{'harvest_date': '',
	                   'cultivar_names': [],
	                   'cultivation_type': ''}],
	     'yield_per_plant':data.get(license_data).get('license').get('yield_per_plan',0),
	     'avg_annual_yield':data.get(license_data).get('license').get('avg_annual_yield',''),
	     'avg_yield_pr_sq_ft':data.get(license_data).get('license').get('yield_per_square_foot_average',0), 
	     'know_yield_per_plant':data.get(license_data).get('license').get('know_yield_per_plant','No'), 
	     'know_yield_per_sq_ft':data.get(license_data).get('license').get('know_yield_per_sq_ft','No'), 
	     'trim_yield_percentage':data.get(license_data).get('license').get('yield_percentage_trim',''),
	     'small_yield_percentage': data.get(license_data).get('license').get('yield_percentage_flower_smalls',''),
	     'flower_yield_percentage':data.get(license_data).get('license').get('flower_yield_percentage','')
    }]

def get_address(company,street,street_2,city,zip_code,state,country):
    """
    ref function-to be edited:['billing_address', 'mailing_address']
    """
    return {
	"company_name":company,
	"street": street,
	"street_line_2": street_2,
	"city": city,
	"zip_code": zip_code,
	"state": state,
	"country": country}



def insert_data_from_crm(user,data):
    """
    Insert available data from crm to database.
    """
    license_list = list(data.keys())
    if license_list:
        for license_data in license_list:
            print('Inserting data for:->',license_data)
            with transaction.atomic():
                #STEP1:insert/create license
                print('1.Inserting license')
                license_obj = License.objects.create(created_by=user,
                                                     license_type=data.get(license_data).get('license').get('license_type',''),
                                                     owner_or_manager='Owner' if data.get(license_data).get('license').get('Owner') else 'Manager',
                                                     legal_business_name=data.get(license_data).get('license').get('legal_business_name',''),
                                                     license_number=data.get(license_data).get('license').get('license_number',''),
                                                     expiration_date=data.get(license_data).get('license').get('expiration_date',''),
                                                     issue_date=data.get(license_data).get('license').get('issue_date',''),
                                                     premises_address=data.get(license_data).get('license').get('premises_address',''),
                                                     premises_county=data.get(license_data).get('license').get('premises_county',''),
                                                     premises_city = data.get(license_data).get('license').get('premises_city',''),
                                                     zip_code=data.get(license_data).get('license').get('zip_code',''),
                                                     premises_apn=data.get(license_data).get('license').get('premises_apn',''),
                                                     premises_state=data.get(license_data).get('license').get('premises_state',''),
                                                     uploaded_sellers_permit_to=data.get(license_data).get('license').get('uploaded_sellers_permit_to',''),
                                                     uploaded_w9_to=data.get(license_data).get('license').get('uploaded_w9_to',''),                               
                                                     uploaded_license_to=data.get(license_data).get('license').get('uploaded_license_to',''),
                                                     is_seller=data.get(license_data).get('is_seller'),
                                                     is_buyer=data.get(license_data).get('is_buyer'),
                                                     profile_category=data.get(license_data).get('vendor_type')[0] if len(data.get(license_data).get('vendor_type')) else None)
                
            with transaction.atomic():
                #STEP2:create License profile
                print('2.Inserting License profile')
                license_profile_obj = LicenseProfile.objects.create(license=license_obj,
                                                                    name=data.get(license_data).get('license_profile').get('name',''),
                                                                    appellation=data.get(license_data).get('license_profile').get('appellation',''),
                                                                    county=data.get(license_data).get('license_profile').get('county',''),
                                                                    region=data.get(license_data).get('license_profile').get('region',''),
                                                                    ethics_and_certification=data.get(license_data).get('license_profile').get('ethics_and_certifications',None),
                                                                    cultivars_of_interest=data.get(license_data).get('license_profile').get('cultivars_of_interest',None),
                                                                    about=data.get(license_data).get('license_profile').get('about',''),
                                                                    product_of_interest=data.get(license_data).get('license_profile').get('product_of_interest',None),
                                                                    transportation=data.get(license_data).get('license_profile').get('transportation_methods',None),
                                                                    issues_with_failed_labtest=data.get(license_data).get('license_profile').get('issues_with_failed_labtest',''),
                                                                    lab_test_issues=data.get(license_data).get('license_profile').get('lab_test_issues',''),
                                                                    agreement_link=data.get(license_data).get('license_profile').get('Contract_Box_Link',''))
                
        
            with transaction.atomic():
                #STEP3:create profile contact
                print("3.Inserting Profle contacts")
                formatted_data = {"company_email":data.get(license_data).get('license_profile').get('company_email',''),
                                  "company_phone":data.get(license_data).get('license_profile').get('company_phone',''),
                                  "website":data.get(license_data).get('license_profile').get('website',''),
                                  "instagram":data.get(license_data).get('license_profile').get('instagram',''),
                                  "facebook":data.get(license_data).get('license_profile').get('facebook',''),
                                  "linkedin":data.get(license_data).get('license_profile').get('linkedIn',''),
                                  "twitter":data.get(license_data).get('license_profile').get('twitter',''),
                                  "no_of_employees":data.get(license_data).get('license_profile').get('no_of_employees',''),
                                  "mailing_address":get_address(data.get(license_data).get('license_profile').get('name',''),
                                                                data.get(license_data).get('license_profile').get('mailing_address_street',''),
                                                                data.get(license_data).get('license_profile').get('mailing_address_street_line_2',''),
                                                                data.get(license_data).get('license_profile').get('mailing_address_city',''),
                                                                data.get(license_data).get('license_profile').get('mailing_address_zip_code',''),
                                                                data.get(license_data).get('license_profile').get('mailing_address_state',''),
                                                                data.get(license_data).get('license_profile').get('mailing_address_country','')),
                                  "billing_address":get_address(data.get(license_data).get('license_profile').get('name',''),
                                                                data.get(license_data).get('license_profile').get('billing_address_street',''),
                                                                data.get(license_data).get('license_profile').get('billing_address_street_line_2',''),
                                                                data.get(license_data).get('license_profile').get('billing_address_city',''),
                                                                data.get(license_data).get('license_profile').get('billing_address_zip_code',''),
                                                                data.get(license_data).get('license_profile').get('billing_address_state',''),
                                                                data.get(license_data).get('license_profile').get('billing_address_country','')),
                                  "employees":get_employee(data)}
                
                pc_obj = ProfileContact.objects.create(license=license_obj,is_draft=False,profile_contact_details=formatted_data)
                
            with transaction.atomic():
                #STEP4:CultivationOverview
                print('4.Inserting Cultivation overview')
                cultivation_obj = CultivationOverview.objects.create(license=license_obj,
                                                                     autoflower=data.get(license_data).get('license_profile').get('Cultivation_Style_Autoflower',False),
                                                                     lighting_type=data.get(license_data).get('license_profile').get('lighting_type',[]),
                                                                     type_of_nutrients=data.get(license_data).get('license_profile').get('type_of_nutrients',[]),
                                                                     overview=[{"canopy_sqf":data.get(license_data).get('license_profile').get('canopy_square_feet',0),
                                                                                "no_of_harvest":data.get(license_data).get('license_profile').get('annual_harvests',0),
                                                                                "plants_per_cycle":data.get(license_data).get('license_profile').get('plants_per_cycle',0)}
                                                                     ])
            with transaction.atomic():
                #STEP5:FinancialOverview
                print('5.Inserting Financial overview')
                FinancialOverview.objects.create(license=license_obj,
                                                 know_annual_budget=data.get(license_data).get('license_profile').get('know_annual_budget',''),
                                                 annual_budget=data.get(license_data).get('license_profile').get('annual_budget',''),
                                                 overview=[{'cost_per_lbs':data.get(license_data).get('license').get('cost_per_lb',''),
                                                            'cost_per_sqf':data.get(license_data).get('license').get('cost_per_square_foot',''),
                                                            'avg_target_price':data.get(license_data).get('license').get('avg_target_price',''),
                                                            'know_cost_per_lbs':data.get(license_data).get('license').get('know_your_cost_per_lb',''),
                                                            'know_cost_per_sqf':data.get(license_data).get('license').get('know_your_cost_per_square_foot',''),
                                                            'trim_target_price':data.get(license_data).get('license').get('price_target_lb_trim',''),
                                                            'small_target_price':data.get(license_data).get('license').get('price_target_lb_flower_smalls',''),
                                                            'bucked_target_price':data.get(license_data).get('license').get('price_target_lb_bucked_untrimmed',''),
                                                            'target_profit_margin':data.get(license_data).get('license').get('profit_margin_target',''),
                                                            'target_profit_percentage': data.get(license_data).get('license').get('target_profit_percentage','')}])
                
            with transaction.atomic():
                #STEP6: CropOverview
                print('6.Inserting Crop overview')
                CropOverview.objects.create(license=license_obj,
                                            process_on_site=data.get(license_data).get('license').get('Can_you_Process_Onsite',''),
                                            overview=get_crop_overview(license_data,data))
    
    
@app.task(queue="general")
def get_from_crm_insert_to_vendor_or_account(user_id):
    """
    async task for existing user.
    """
    instance = User.objects.filter(id=user_id)
    parsed_names = [ re.match(r"^(.*) -\d*$",i).group(1) for i in instance[0].legal_business_name]        
    if instance:
        if parsed_names:
            for business in parsed_names:
                response_data = get_records_from_crm(business)
                if not response_data.get('error'):
                    insert_data_from_crm(instance[0],response_data)
                    

@app.task(queue="general")
def get_license_from_crm_insert_to_db(user_id,license_number):
    """
    async task for existing user.Insert/create license based on license number.
    """
    instance = User.objects.filter(id=user_id)
    if instance:
        response_data = get_records_from_crm(license_number=license_number)
        if not response_data.get('error'):
            insert_data_from_crm(instance[0],response_data)                    
    


