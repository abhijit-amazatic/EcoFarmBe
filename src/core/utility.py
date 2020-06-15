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
from account.models import *
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
    
def notify_admins_on_accounts_registration(email,company):
    """
    Notify admins on slack & email about new Accounts registration.
    """
    msg = "<!channel>New Account is registered with us with the company name as  - %s under the EmailID `%s`.Please review and approve from admin Panel!" % (company, email)
    slack.chat.post_message(settings.SLACK_CHANNEL_NAME,msg, as_user=True)
    mail_send("account-register.html",{'link':company,'mail':email},"New Account profile registration.", recipient_list=settings.ADMIN_EMAIL)
    
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
    role_map = {"License Owner":"license_owner","Farm Manager":"farm_manager","Sales/Inventory":"sales_or_inventory","Logistics":"logistics","Billing":"billing","Owner":"owner"}
    pro_contact_obj = ProfileContact.objects.filter(id=profile_contact_id)
    if pro_contact_obj:
        employee_data = pro_contact_obj[0].profile_contact_details.get('employees')
              
        for employee in employee_data:
            obj, created = User.objects.get_or_create(email=employee['employee_email'],
                                                      defaults={'email':employee['employee_email'],
                                                                'username':employee['employee_name'],
                                                                'phone':employee['phone'],
                                                                'is_verified':False,
                                                                'existing_member':True})
            if created:
                if not VendorUser.objects.filter(user_id=obj.id, vendor_id=vendor_obj_id).exists():
                    extracted_role = role_map.get(employee['roles'][0])
                    VendorUser(user_id=obj.id, vendor_id=vendor_obj_id,role=employee['roles'][0]).save()
                    #notify_farm_user(obj.email, pro_contact_obj[0].profile_contact_details.get('farm_name'))
                    #notify_admins_on_vendors_registration(obj.email,pro_contact_obj[0].profile_contact_details.get('farm_name'))
                    
def extract_role(role):
    """
    Map role for existing user according to database choices.
    """
    role_map = {"License Owner":"license_owner","Farm Manager":"farm_manager","Sales/Inventory":"sales_or_inventory","Logistics":"logistics","Billing":"billing","Owner":"owner"}
    extracted_role =  [value for key, value in role_map.items() if role.lower() in key.lower()]
    if extracted_role:
        return extracted_role
    else:
        return ["farm_manager"]

def harvest_dates(data,param):
    """
    Extract harvest dates based on type.
    """
    return [value for key, value in data.get('processing_config').items() if param in key.lower() and value]

    
def extract_processing_data(cultivation_type,data,cultivars):
    """
    extract processing data according to inputs
    """
    if cultivation_type == "mixed_light":
        return {"flower_yield_percentage":data.get('processing_config').get('po_mixed_light.flower_yield_percentage',0),
		"small_yield_percentage":data.get('processing_config').get('po_mixed_light.small_yield_percentage',0),
		"trim_yield_percentage":data.get('processing_config').get('po_mixed_light.trim_yield_percentage',0),
		"yield_per_plant":data.get('processing_config').get('po_mixed_light.yield_per_plant',0),
		"avg_yield_per_sq_ft": data.get('processing_config').get('po_mixed_light.avg_yield_pr_sq_ft',0),
                "cultivars": [{"harvest_date":date, "cultivar_names": cultivars,"cultivation_type":"mixed_light"}
                              for date in harvest_dates(data,'po_mixed_light.cultivars_')]}
    elif cultivation_type == "indoor":
        return {"flower_yield_percentage":data.get('processing_config').get('po_indoor.flower_yield_percentage',0),
		"small_yield_percentage":data.get('processing_config').get('po_indoor.small_yield_percentage',0),
		"trim_yield_percentage":data.get('processing_config').get('po_indoor.trim_yield_percentage',0),
		"yield_per_plant":data.get('processing_config').get('po_indoor.yield_per_plant',0),
		"avg_yield_per_sq_ft": data.get('processing_config').get('po_indoor.avg_yield_pr_sq_ft',0),
                "cultivars": [{"harvest_date":date, "cultivar_names": cultivars,"cultivation_type":"indoor"}
                              for date in harvest_dates(data,'po_indoor.cultivars_')]}
    elif cultivation_type == "outdoor_autoflower":
        return {"flower_yield_percentage":data.get('processing_config').get('po_outdoor_autoflower.flower_yield_percentage',0),
		"small_yield_percentage":data.get('processing_config').get('po_outdoor_autoflower.small_yield_percentage',0),
		"trim_yield_percentage":data.get('processing_config').get('po_outdoor_autoflower.trim_yield_percentage',0),
		"yield_per_plant":data.get('processing_config').get('po_outdoor_autoflower.yield_per_plant',0),
		"avg_yield_per_sq_ft": data.get('processing_config').get('po_outdoor_autoflower.avg_yield_per_sq_ft',0),
                "cultivars": [{"harvest_date":date, "cultivar_names": cultivars,"cultivation_type":"outdoor_autoflower"}
                              for date in harvest_dates(data,'po_outdoor_autoflower.cultivars_')]}
    elif cultivation_type == "outdoor_full_season":
        return {"flower_yield_percentage":data.get('processing_config').get('po_outdoor_full_season.flower_yield_percentage',0),
		"small_yield_percentage":data.get('processing_config').get('po_outdoor_full_season.small_yield_percentage',0),
		"trim_yield_percentage":data.get('processing_config').get('po_outdoor_full_season.trim_yield_percentage',0),
		"yield_per_plant":data.get('processing_config').get('po_outdoor_full_season.yield_per_plant',0),
		"avg_yield_per_sq_ft": data.get('processing_config').get('po_outdoor_full_season.avg_yield_pr_sq_ft',0),
                "cultivars": [{"harvest_date":date, "cultivar_names": cultivars,"cultivation_type":"outdoor_full_season"}
                              for date in harvest_dates(data,'po_outdoor_full_season.cultivars_')]}
        
def extract_financial_data(cultivation_type,data):
    """
    extract financial data according to inputs
    """
    if cultivation_type == "mixed_light":
        return {"target_profit_margin":data.get('financial_details').get('fd_mixed_light.target_profit_margin',''),
		"know_cost_per_lbs":data.get('financial_details').get('fd_mixed_light.know_cost_per_lbs',''),
		"cost_per_lbs":data.get('financial_details').get('fd_mixed_light.cost_per_lbs',''),
		"know_cost_per_sqf":data.get('financial_details').get('fd_mixed_light.know_cost_per_sqf',''),
		"cost_per_sqf":data.get('financial_details').get('fd_mixed_light.cost_per_sqf',''),
		"tops_target_price":data.get('financial_details').get('fd_mixed_light.tops_target_price',''),
		"small_target_price":data.get('financial_details').get('fd_mixed_light.small_target_price',''),
		"trim_target_price":data.get('financial_details').get('fd_mixed_light.trim_target_price',''),
		"bucked_untrimmed":data.get('financial_details').get('fd_mixed_light.bucked_untrimmed','')
		}
    elif cultivation_type == "outdoor_full_season":
        return {"target_profit_margin":data.get('financial_details').get('fd_outdoor_full_season.target_profit_margin',''),
	        "know_cost_per_lbs":data.get('financial_details').get('fd_outdoor_full_season.know_cost_per_lbs',''),
	        "cost_per_lbs":data.get('financial_details').get('fd_outdoor_full_season.cost_per_lbs',''),
		"know_cost_per_sqf":data.get('financial_details').get('fd_outdoor_full_season.know_cost_per_sqf',''),
		"cost_per_sqf":data.get('financial_details').get('fd_outdoor_full_season.cost_per_sqf',''),
		"tops_target_price":data.get('financial_details').get('fd_outdoor_full_season.tops_target_price',''),
		"small_target_price":data.get('financial_details').get('fd_outdoor_full_season.small_target_price',''),
		"trim_target_price":data.get('financial_details').get('fd_outdoor_full_season.trim_target_price',''),
		"bucked_untrimmed":data.get('financial_details').get('fd_outdoor_full_season.bucked_untrimmed','')
		}
    elif cultivation_type == "outdoor_autoflower":
        return {"target_profit_margin":data.get('financial_details').get('fd_outdoor_autoflower.target_profit_margin',''),
	        "know_cost_per_lbs":data.get('financial_details').get('fd_outdoor_autoflower.know_cost_per_lbs',''),
	        "cost_per_lbs":data.get('financial_details').get('fd_outdoor_autoflower.cost_per_lbs',''),
		"know_cost_per_sqf":data.get('financial_details').get('fd_outdoor_autoflower.know_cost_per_sqf',''),
		"cost_per_sqf":data.get('financial_details').get('fd_outdoor_autoflower.cost_per_sqf',''),
		"tops_target_price":data.get('financial_details').get('fd_outdoor_autoflower.tops_target_price',''),
		"small_target_price":data.get('financial_details').get('fd_outdoor_autoflower.small_target_price',''),
		"trim_target_price":data.get('financial_details').get('fd_outdoor_autoflower.trim_target_price',''),
		"bucked_untrimmed":data.get('financial_details').get('fd_outdoor_autoflower.bucked_untrimmed','')
		}
    elif cultivation_type == "indoor":
        return {"target_profit_margin":data.get('financial_details').get('fd_indoor.target_profit_margin',''),
	        "know_cost_per_lbs":data.get('financial_details').get('fd_indoor.know_cost_per_lbs',''),
	        "cost_per_lbs":data.get('financial_details').get('fd_indoor.cost_per_lbs',''),
		"know_cost_per_sqf":data.get('financial_details').get('fd_indoor.know_cost_per_sqf',''),
		"cost_per_sqf":data.get('financial_details').get('fd_indoor.cost_per_sqf',''),
		"tops_target_price":data.get('financial_details').get('fd_indoor.tops_target_price',''),
		"small_target_price":data.get('financial_details').get('fd_indoor.small_target_price',''),
		"trim_target_price":data.get('financial_details').get('fd_indoor.trim_target_price',''),
		"bucked_untrimmed":data.get('financial_details').get('fd_indoor.bucked_untrimmed','')
		}

def extract_overview_data(cultivation_type,data):
    """
    extract overview data according to inputs.
    """
    if cultivation_type == "mixed_light":
        return {"canopy_sqf":data.get('profile_overview').get('mixed_light.canopy_sqf',0),
                "no_of_harvest":data.get('profile_overview').get('mixed_light.no_of_harvest',0),
                "plants_per_cycle":data.get('profile_overview').get('mixed_light.plants_per_cycle',0)}
    elif cultivation_type == "indoor":
        return {"canopy_sqf":data.get('profile_overview').get('indoor.canopy_sqf',0),
                "no_of_harvest":data.get('profile_overview').get('indoor.no_of_harvest',0),
                "plants_per_cycle":data.get('profile_overview').get('indoor.plants_per_cycle',0)}
    elif cultivation_type == "outdoor_full_season":
        return {"canopy_sqf":data.get('profile_overview').get('outdoor_full_season.canopy_sqf',0),
                "no_of_harvest":data.get('profile_overview').get('outdoor_full_season.no_of_harvest',0),
                "plants_per_cycle":data.get('profile_overview').get('outdoor_full_season.plants_per_cycle',0)}
    elif cultivation_type == "outdoor_autoflower":
        return {"canopy_sqf":data.get('profile_overview').get('outdoor_autoflower.canopy_sqf',0),
                "no_of_harvest":data.get('profile_overview').get('outdoor_autoflower.no_of_harvest',0),
                "plants_per_cycle":data.get('profile_overview').get('outdoor_autoflower.plants_per_cycle',0)}
    
    
    
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
            obj,created = Vendor.objects.get_or_create(ac_manager=user,vendor_category=vendor)
            if not VendorUser.objects.filter(user_id=user.id, vendor=obj.id).exists():
                VendorUser.objects.create(user_id=user.id, vendor_id=obj.id,role='owner')         
            vendor_user=VendorUser.objects.get(user_id=user.id,vendor=obj)
            if vendor_user.role == 'owner' and user.existing_member and vendor == "cultivation":
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
                                                             uploaded_sellers_permit_to=key.get('uploaded_sellers_permit_to',''),
                                                             uploaded_w9_to=key.get('uploaded_w9_to',''),
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
                                      "employees":[{"employee_name":data.get('profile_contact').get('employees',{}).get(contact,'')['employee_name'],
                                                    "employee_email":data.get('profile_contact').get('employees',{}).get(contact,'')['employee_email'] ,
                                                    "phone":data.get('profile_contact').get('employees',{}).get(contact,'')['phone'],
                                                    "roles":extract_role(contact.split()[0])} for contact in contacts]}
                    pc_step2, created = ProfileContact.objects.get_or_create(vendor_profile_id=vp.id, is_draft=False,profile_contact_details = formatted_data)
                    if created:
                        add_users_to_system.delay(pc_step2.id,vp.id,obj.id)
                    print("STEP2 Profile contact fetched in DB")
                with transaction.atomic():
                    profile_data = {"lighting_type":data.get('profile_overview').get('lighting_type',[]),
                                    "type_of_nutrients":data.get('profile_overview').get('type_of_nutrients',''),
                                    "interested_in_growing_genetics":data.get('profile_overview').get('interested_in_growing_genetics',''),
                                    "issues_with_failed_lab_tests":data.get('profile_overview').get('issues_with_failed_lab_tests',''),
                                    "lab_test_issues":data.get('profile_overview').get('lab_test_issues',''),
                                    "autoflower":data.get('profile_overview').get('autoflower',''),
                                    "full_season":data.get('profile_overview').get('full_season',''),
                                    "outdoor_full_season":extract_overview_data('outdoor_full_season',data),
                                    "outdoor_autoflower":extract_overview_data('outdoor_autoflower',data),
                                    "mixed_light":extract_overview_data('mixed_light',data),
                                    "indoor":extract_overview_data('indoor',data)} 
                    #STEP3 - add profile_overview
                    po_step3 = ProfileOverview.objects.get_or_create(vendor_profile_id=vp.id, is_draft=False, profile_overview=profile_data)
                    print("STEP3 Profile Overview fetched in DB")
                with transaction.atomic():         
                    #STEP4 - add  processing_config
                    cultivars_data = data.get('processing_config').get('cultivars','')
                    if cultivars_data:
                        cultivars = cultivars_data.split(',')
                    else:
                        cultivars = ['']
                    processing_data = {"mixed_light":extract_processing_data('mixed_light',data,cultivars),
                                       "indoor":extract_processing_data('indoor',data,cultivars), 
		                       "outdoor_autoflower":extract_processing_data('outdoor_autoflower',data,cultivars),
                                       "outdoor_full_season":extract_processing_data('outdoor_full_season',data,cultivars),
                                       "process_on_site": data.get('processing_config').get('process_on_site','')}
                    pc_step4 = ProcessingOverview.objects.get_or_create(vendor_profile_id=vp.id, is_draft=False, processing_config=processing_data)
                    print("STEP4 Proc.Overview fetched in DB")
                with transaction.atomic():   
                    #STEP5 - add financial details
                    financial_data = {"annual_revenue_2019":data.get('financial_details').get('fd_annual_revenue_2019',''),
                                      "projected_2020_revenue":data.get('financial_details').get('fd_projected_2020_revenue',''),
                                      "yearly_budget":data.get('financial_details').get('fd_yearly_budget',''),
                                      "mixed_light":extract_financial_data('mixed_light',data),
                                      "outdoor_full_season":extract_financial_data('outdoor_full_season',data),
                                      "outdoor_autoflower":extract_financial_data('outdoor_autoflower',data),
                                      "indoor":extract_financial_data('indoor',data)}
                    fd_step5 = FinancialOverview.objects.get_or_create(vendor_profile_id=vp.id,is_draft=False, financial_details=financial_data)
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


@app.task(queue="general")
def send_async_account_approval_mail(account_id):
    """
    Async email send for after account approval.
    """
    account_obj = Account.objects.filter(id=account_id)
    
    if account_obj:
        ac_manager = account_obj[0].ac_manager.email
        mail_send("account-approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login'},"Account Profile Approved.", ac_manager)
        
@app.task(queue="general")        
def send_async_user_approval_mail(user_id):
    """
    Async email send for after user approval.
    """
    user = User.objects.filter(id=user_id)    
    mail_send("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login'},"Account Approved.", user[0].email)

@app.task(queue="general")            
def notify_employee_admin_to_verify_and_reset(vendor_id,vendor_profile_id):
    """
    Notify farm employee to verify and set password for account.Notfiy admin to approve user
    """
    vendor_users = VendorUser.objects.filter(vendor=vendor_id,user__is_approved=False, user__is_verified=False).select_related()
    profile_contact = ProfileContact.objects.filter(vendor_profile_id=vendor_profile_id)
    for vendor_user in vendor_users:
        try:
            # send email verification link to farm user
            link = get_encrypted_data(vendor_user.user.email)
            mail_send("verification-send.html",{'link': link},"Eco-Farm Verification.",vendor_user.user.email)
            #inform admins to approve farm user
            notify_admins_on_vendors_registration(vendor_user.user.email,profile_contact[0].profile_contact_details.get('farm_name'))
            #notify user to set password
            notify_farm_user(vendor_user.user.email, profile_contact[0].profile_contact_details.get('farm_name'))
        except Exception as e:
            print("Exception on profile aproval notification",e)
    

def extract_account_employees_data(data,param):
    """
    Format and extract data according to models
    """
    if param == "employees":
        return [{"phone":data.get('contact_info',{}).get('owner_phone'),
                 "role": "Owner",
                 "employee_name":data.get('contact_info',{}).get('owner_name'),
                 "employee_email":data.get('contact_info',{}).get('owner_email')},
                {"phone":data.get('contact_info',{}).get('logistic_manager_phone'),
                 "role": "Logistics",
                 "employee_name":data.get('contact_info',{}).get('logistic_manager_name'),
                 "employee_email":data.get('contact_info',{}).get('logistic_manager_email')}]
    elif param == "address":
        return  {
	    "billing_compony_name":data.get('contact_info',{}).get('billing_compony_name'),
	    "billing_street":data.get('contact_info',{}).get('billing_street'),
	    "billing_street_line_2":data.get('contact_info',{}).get('billing_street_line_2'),
	    "billing_city":data.get('contact_info',{}).get('billing_city'),
	    "billing_zip_code":data.get('contact_info',{}).get('billing_zip_code'),
	    "billing_state":data.get('contact_info',{}).get('billing_state'),
	}


@app.task(queue="general")
def insert_data_for_accounts(user,account_type,data):
    """
    For existing user, to insert records to perticular accounts use this function.
    """
    try:
        for account in account_type:
            category = [k for k,v in NOUN_PROCESS_MAP.items() if v.lower() == account.lower()]
            obj,created = Account.objects.get_or_create(ac_manager=user,account_category=category[0])
            if not AccountUser.objects.filter(user_id=user.id, account=obj.id).exists():
                AccountUser.objects.create(user_id=user.id, vendor_id=obj.id,role='owner')         
            account_user=AccountUser.objects.get(user_id=user.id,account=obj)
            if account_user.role == 'owner' and user.existing_member:
                """
                Only first owner can pull & store data as others will have access anyways.
                """
                act, created = AccountLicense.objects.get_or_create(account=obj) #for step1
                print('account to be updated->', ac)
                with transaction.atomic():
                    #STEP1
                    if data.get('licenses'):
                        AccountLicense.objects.bulk_create([AccountLicense(account_id=act.id,
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
                                                             uploaded_license_to=key.get('uploaded_license_to','')) for key in data.get('licenses')], ignore_conflicts=False)
                        print("STEP1 Account License fetched in DB")
                with transaction.atomic():   
                    #STEP2 - add account basic details
                    account_step2 = AccountBasicProfile.objects.get_or_create(account_id=act.id,
                                                                              is_draft=False,
                                                                              company_name=data.get('basic_profile',{}).get('company_name'),
                                                                              about_company=data.get('basic_profile',{}).get('about'),
                                                                              region=data.get('basic_profile',{}).get('region'),
                                                                              preferred_payment=",".join(data.get('basic_profile',{}).get('preferred_payment')),
                                                                              cultivars_of_interest=data.get('basic_profile',{}).get('cultivars_of_interest',[]),
                                                                              ethics_and_certification=data.get('basic_profile',{}).get('ethics_and_certification',[]),
                                                                              product_of_interest=data.get('basic_profile',{}).get('product_of_interest',[]),
                                                                              provide_transport=data.get('basic_profile',{}).get('provide_transport',[]))
                    print("STEP2 basic data fetched in DB")
                    
                with transaction.atomic():     
                    #STEP3-add account contact data
                    account_step3, created = AccountContactInfo.objects.get_or_create(account_id=act.id, is_draft=False,
                                                                                      company_phone=data.get('contact_info',{}).get('company_phone'),
                                                                                      website=data.get('contact_info',{}).get('website'),
                                                                                      company_email=data.get('contact_info',{}).get('company_email'),
                                                                                      employees=extract_account_employees_data(data,'employees'),
                                                                                      instagram=data.get('contact_info',{}).get('instagram'),
                                                                                      linked_in=data.get('contact_info',{}).get('linked_in'),
                                                                                      twitter=data.get('contact_info',{}).get('twitter'),
                                                                                      facebook=data.get('contact_info',{}).get('facebook'),
                                                                                      billing_address=extract_account_employees_data(data,'address'),
                                                                                      mailing_address=extract_account_employees_data(data,'employees'))
                    if created:
                        pass #add_users_to_system.delay(account_step3.id,act.id,obj.id)
                    print("STEP3 account contact fetched in DB")
    except Exception as e:
        print('Exception in accounts insertation\n',e)        
