from django.db import transaction
from core.mailer import mail, mail_send
from django.contrib.auth import get_user_model
from django.conf import settings
from brand.models import (
    License,
    LicenseProfile,
    ProfileContact,
    CultivationOverview,
    FinancialOverview,
    CropOverview,
    OrganizationRole,
)

User = get_user_model()

class ErrorDataNotFound(Exception):
    pass

class ErrorNoAssociationFound(Exception):
    pass

def extract_map_role(data, existing_roles):
    role_map = {
        "Owner":"License Owner",
        "Cultivation Manager":"Farm Manager",
        "Sales Manager":"Sales/Inventory",
        "Logistics Manager":"Logistics",
        "Billing / Accounting":"Billing",
    }
    updated_roles = [role_map.get(r, r) for r in data]
    return  [r for r in updated_roles if r in existing_roles] or ['Employee']

def get_employee(data_l_p, existing_roles):
    """
    structure employee according to db format & insert empty data also.
    (currently inserted empty contacts)
    """
    tmp_data = []
    employees_list = data_l_p.get('employees')
    if employees_list:
        for employee in employees_list:
            tmp_data.append({
                "employee_name": employee.get('Full_Name'),
                "employee_email": employee.get('Email'),
                "phone": employee.get('Phone', ""),
                "roles": extract_map_role(employee.get('Contact_Company_Role', []), existing_roles),
            })
    return tmp_data

def get_address(company, street, street_2, city, zip_code, state, country):
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
        "country": country,
    }



def insert_data_from_crm(user, response_data, license_id, license_number):
    """
    Insert available data from crm to database.
    """
    try:
        organization = response_data.pop('organization')
    except KeyError:
        organization = None
    if response_data and isinstance(response_data, dict):
        data =  response_data.get(license_number)
        if data:
        # for license_number, data in response_data.items():
            data_l = data.get('license', {})
            data_l_p = data.get('license_profile', {})
            print(f'Inserting data for:-> {license_number}')
            with transaction.atomic():
                #STEP1:insert/create license
                print('1.Inserting license')
                # license_obj = License.objects.create(
                #     created_by=user,
                #     zoho_crm_id=data_l.get('license_id',''),
                #     license_type=data_l.get('license_type',''),
                #     owner_or_manager='Owner' if data_l.get('Owner') else 'Manager',
                #     legal_business_name=data_l.get('legal_business_name',''),
                #     license_number=data_l.get('license_number',''),
                #     expiration_date=data_l.get('expiration_date',''),
                #     issue_date=data_l.get('issue_date',''),
                #     premises_address=data_l.get('premises_address',''),
                #     premises_county=data_l.get('premises_county',''),
                #     premises_city = data_l.get('premises_city',''),
                #     zip_code=data_l.get('zip_code',''),
                #     premises_apn=data_l.get('premises_apn',''),
                #     premises_state=data_l.get('premises_state',''),
                #     uploaded_sellers_permit_to=data_l.get('uploaded_sellers_permit_to',''),
                #     uploaded_w9_to=data_l.get('uploaded_w9_to',''),
                #     uploaded_license_to=data_l.get('uploaded_license_to',''),
                #     is_seller=data.get('is_seller'),
                #     is_buyer=data.get('is_buyer'),
                #     profile_category=(
                #       data.get('vendor_type')[0] if len(data.get('vendor_type')) else None
                #     ),
                # )
                license_obj = License.objects.get(id=license_id)

            with transaction.atomic():
                #STEP2:create License profile
                print('2.Inserting License profile')
                data_l_p__owner = data_l_p.get('Owner') or {}
                LicenseProfile.objects.create(
                    license=license_obj,
                    zoho_crm_id=data_l_p.get('profile_id', ''),
                    name=data_l_p.get('name', ''),
                    appellation=data_l_p.get('appellation', ''),
                    county=data_l_p.get('county', ''),
                    region=data_l_p.get('region', ''),
                    ethics_and_certification=data_l_p.get('ethics_and_certifications', []),
                    cultivars_of_interest=data_l_p.get('cultivars_of_interest', []),
                    about=data_l_p.get('about', ''),
                    product_of_interest=data_l_p.get('product_of_interest', []),
                    transportation=data_l_p.get('transportation_methods', None),
                    issues_with_failed_labtest=data_l_p.get('issues_with_failed_labtest', ''),
                    lab_test_issues=data_l_p.get('lab_test_issues', ''),
                    agreement_link=data_l_p.get('Contract_Box_Link', ''),
                    preferred_payment=data_l_p.get('preferred_payment', []),
                    bank_routing_number=data_l_p.get('bank_routing_number', ''),
                    bank_account_number=data_l_p.get('bank_account_number', ''),
                    bank_name=data_l_p.get('bank_name', ''),
                    bank_street=data_l_p.get('bank_street', ''),
                    bank_city=data_l_p.get('bank_city', ''),
                    bank_zip_code=data_l_p.get('bank_zip_code', ''),
                    crm_owner_id=data_l_p__owner.get('id', ''),
                    crm_owner_email=data_l_p__owner.get('email', ''),
                )

            with transaction.atomic():
                #STEP3:create profile contact
                print("3.Inserting Profile contacts")
                existing_roles = list(
                    OrganizationRole.objects.filter(organization=license_obj.organization).values_list('name', flat=True)
                )
                formatted_data = {
                    "company_email":data_l_p.get('company_email', ''),
                    "company_phone":data_l_p.get('company_phone', ''),
                    "website":data_l_p.get('website', ''),
                    "instagram":data_l_p.get('instagram', ''),
                    "facebook":data_l_p.get('facebook', ''),
                    "linkedin":data_l_p.get('linkedIn', ''),
                    "twitter":data_l_p.get('twitter', ''),
                    "no_of_employees":data_l_p.get('no_of_employees', ''),
                    "mailing_address":get_address(
                        data_l_p.get('name', ''),
                        data_l_p.get('mailing_address_street', ''),
                        data_l_p.get('mailing_address_street_line_2', ''),
                        data_l_p.get('mailing_address_city', ''),
                        data_l_p.get('mailing_address_zip_code', ''),
                        data_l_p.get('mailing_address_state', ''),
                        data_l_p.get('mailing_address_country', ''),
                    ),
                    "billing_address":get_address(
                        data_l_p.get('name', ''),
                        data_l_p.get('billing_address_street', ''),
                        data_l_p.get('billing_address_street_line_2', ''),
                        data_l_p.get('billing_address_city', ''),
                        data_l_p.get('billing_address_zip_code', ''),
                        data_l_p.get('billing_address_state', ''),
                        data_l_p.get('billing_address_country', '')
                    ),
                    "employees":get_employee(data_l_p, existing_roles),
                }

                ProfileContact.objects.create(
                    license=license_obj,
                    is_draft=False,
                    profile_contact_details=formatted_data
                )

            with transaction.atomic():
                #STEP4:CultivationOverview
                print('4.Inserting Cultivation overview')
                CultivationOverview.objects.create(
                    license=license_obj,
                    autoflower=data_l_p.get('Cultivation_Style_Autoflower', False),
                    lighting_type=data_l.get('lighting_type') or data_l_p.get('lighting_type', []),
                    type_of_nutrients=data_l.get('types_of_nutrients') or data_l_p.get('type_of_nutrients', []),
                    overview=[
                        {
                            "canopy_sqf":data_l.get('canopy_square_feet_mixed_light', 0),
                            "no_of_harvest":data_l.get('annual_harvests_mixed_light', 0),
                            "plants_per_cycle":data_l.get('plants_per_cycle_mixed_light', 0)
                        },
                        {
                            "canopy_sqf":data_l.get('canopy_square_feet_autoflower', 0),
                            "no_of_harvest":data_l.get('annual_harvests_autoflower', 0),
                            "plants_per_cycle":data_l.get('plants_per_cycle_autoflower', 0)
                        },
                    ],
                )
            with transaction.atomic():
                #STEP5:FinancialOverview
                print('5.Inserting Financial overview')
                FinancialOverview.objects.create(
                    license=license_obj,
                    know_annual_budget=data_l_p.get('know_annual_budget', ''),
                    annual_budget=data_l_p.get('annual_budget', ''),
                    overview=[{
                        'cost_per_lbs':data_l.get('cost_per_lb', ''),
                        'cost_per_sqf':data_l.get('cost_per_square_foot', ''),
                        'avg_target_price':data_l.get('avg_target_price', ''),
                        'know_cost_per_lbs':data_l.get('know_your_cost_per_lb', ''),
                        'know_cost_per_sqf':data_l.get('know_your_cost_per_square_foot', ''),
                        'trim_target_price':data_l.get('price_target_lb_trim', ''),
                        'small_target_price':data_l.get('price_target_lb_flower_smalls', ''),
                        'bucked_target_price':data_l.get('price_target_lb_bucked_untrimmed', ''),
                        'target_profit_margin':data_l.get('profit_margin_target', ''),
                        'target_profit_percentage': data_l.get('target_profit_percentage', ''),
                    }],
                )

            with transaction.atomic():
                #STEP6: CropOverview
                print('6.Inserting Crop overview')
                CropOverview.objects.create(
                    license=license_obj,
                    process_on_site=data_l.get('Can_you_Process_Onsite', ''),
                    overview=[{
                        'cultivars':[{
                            'harvest_date': '',
                            'cultivar_names': [],
                            'cultivation_type': '',
                        }],
                        'yield_per_plant':data_l.get('yield_per_plan', 0),
                        'avg_annual_yield':data_l.get('avg_annual_yield', ''),
                        'avg_yield_pr_sq_ft':data_l.get('yield_per_square_foot_average', 0),
                        'know_yield_per_plant':data_l.get('know_yield_per_plant', 'No'),
                        'know_yield_per_sq_ft':data_l.get('know_yield_per_sq_ft', 'No'),
                        'trim_yield_percentage':data_l.get('yield_percentage_trim', ''),
                        'small_yield_percentage': data_l.get('yield_percentage_flower_smalls', ''),
                        'flower_yield_percentage':data_l.get('flower_yield_percentage', '')
                    }],
                )
            print('Updating license is_data_fetching_complete flag')
            license_obj.is_data_fetching_complete=True
            license_obj.save()
        return {"success":"Data successfully fetched to DB"}


def send_onboarding_data_fetch_verification_mail(instance, user_id):
    """
    docstring
    """
    user_obj = User.objects.get(id=user_id)
    full_name = user_obj.full_name or f'{user_obj.first_name} {user_obj.last_name}'
    context = {
        'owner_full_name':  instance.owner_name,
        'user_full_name':  full_name,
        'user_email': user_obj.email,
        'license': f"{instance.license_number} | {instance.legal_business_name}",
        'otp': instance.generate_otp_str(),
    }
    email_overide = getattr(settings, 'ONBOARDING_DATA_FETCH_EMAIL_OVERRIDE', [])
    if email_overide:
        for email in email_overide:
            mail_send(
                "license_owner_datapoputalaion_otp.html",
                context,
                "Thrive Society License Data Population verification.",
                email.strip(),
            )
    else:
        mail_send(
            "license_owner_datapoputalaion_otp.html",
            context,
            "Thrive Society License Data Population verification.",
            instance.owner_email,
        )
