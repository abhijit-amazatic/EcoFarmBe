#key- field from CRM, value- field from user model.
CRM_FORMAT  = {
    "Contacts": {
        "Email": "email",
        "First_Name": "first_name",
        "Last_Name": "last_name",
        "Full_Name": "full_name",
        "Other_Country": "country",
        "Other_State": "state",
        "Date_Of_Birth": "date_of_birth",
        "Other_City": "city",
        "Other_Zip": "zip_code",
        "Phone": "phone"
    },
    "Vendors": {
        "db_id": "db_id",
        "Layout": "layout_parse",
        #Farm Profile
        "Vendor_Name": "farm_name",
        "About_Company": "about_company",
        "Vendor_Type": "vendor_type_parse",
        "County": "primary_county",
        "Region": "region",
        "Appellations": "appellation",
        "Special_Certifications": "ethics_and_certifications",
        "Transportation_Method": "transportation",
        #Compilance
        "Licenses_List": "licenses",
        #Farm Contact
        "Phone": "company_phone",
        "Email": "company_email",
        "Website": "website",
        "LinkedIn": "linkedin_url",
        "Instagram": "instagram_url",
        "Facebook": "facebook_url",
        "Twitter": "twitter_url",
        "Contact_1": "employees_parse", # Cultivation Manager
        "Contact_2": "employees_parse", # Logistics Manager
        "Contact_3": "employees_parse", # Quality Assurance Manager
        "Owner1": "employees_parse", # Owner
        "Number_of_Employees": "no_of_employees",
        #Questionnaire
        "po_cultivars": "po_cultivars_parse",
        "Indoor_Mixed_Lighting_Type": "lighting_type",
        "Types_of_Nutrients_Used": "type_of_nutrients",
        "Would_you_grow_genetics_suggested_by_Thrive": "interested_in_growing_genetics",
        "Issues_with_Failed_Lab_Tests": "lab_test_issues",
        #Mixed Light
        "Total_Canopy_Space": "mixed_light.canopy_sqf_parse",
        "Annual_Harvests": "mixed_light.no_of_harvest_parse",
        "How_many_clones_total_will_you_need_for_the_year": "How_many_clones_total_will_you_need_for_the_year",
        "Plants_per_Cycle_Mixed_Light": "mixed_light.plants_per_cycle_parse",
        "Yield_Sqf_Average_Mixed_Light": "po_mixed_light.avg_yield_pr_sq_ft_parse",
        "Expected_Yield_Per_Plant": "po_mixed_light.yield_per_plant_parse",
        "Annual_Production_Lbs": "po_mixed_light.avg_annual_yield",
        "Flower": "po_mixed_light.flower_yield_percentage_parse",
        "Smalls": "po_mixed_light.small_yield_percentage_parse",
        "Trim": "po_mixed_light.trim_yield_percentage_parse",
        "Know_your_Cost_per_Sqf": "fd_mixed_light.know_cost_per_sqf_parse",
        "Cost_per_Sqf": "fd_mixed_light.cost_per_sqf_parse",
        "Know_your_Cost_per_LB": "fd_mixed_light.know_cost_per_lbs_parse",
        "Cost_per_LB": "fd_mixed_light.cost_per_lbs_parse",
        "Flower_Target_Price_Lb": "fd_mixed_light.tops_target_price_parse",
        "Smalls_Target_Price_Lb": "fd_mixed_light.small_target_price_parse",
        "Trim_Target_Price_Lb": "fd_mixed_light.trim_target_price_parse",
        "Bucked_Untrimmed_Target_Price_Lb": "fd_mixed_light.bucked_untrimmed_parse",
        "Target_Profit_Margin_Mixed_Light": "fd_mixed_light.target_profit_margin_parse",
        "Harvest_1": "po_mixed_light.cultivars_1_parse",
        "Harvest_2": "po_mixed_light.cultivars_2_parse",
        "Harvest_3": "po_mixed_light.cultivars_3_parse",
        "Harvest_4": "po_mixed_light.cultivars_4_parse",
        "Harvest_5": "po_mixed_light.cultivars_5_parse",
        "Harvest_6": "po_mixed_light.cultivars_6_parse",
        "Harvest_7": "po_mixed_light.cultivars_7_parse",
        "Harvest_8": "po_mixed_light.cultivars_8_parse",
        "Harvest_9": "po_mixed_light.cultivars_9_parse",
        "Harvest_10": "po_mixed_light.cultivars_10_parse",
        "Harvest_11": "po_mixed_light.cultivars_11_parse",
        "Harvest_12": "po_mixed_light.cultivars_12_parse",
        #Outdoor
        "Full_Season": "full_season_parse",
        "Canopy_Sqf_Outdoor": "outdoor_full_season.canopy_sqf_parse",
        "Annual_Harvest_Outdoor": "outdoor_full_season.no_of_harvest_parse",
        "Plants_per_Cycle_Outdoor": "outdoor_full_season.plants_per_cycle_parse",
        "Yield_Sqf_Average_Outdoor": "po_outdoor_full_season.avg_yield_pr_sq_ft_parse",
        "Yield_Plant_Average_Outdoor": "po_outdoor_full_season.yield_per_plant_parse",
        "Yield_Per_Cycle_Indoor": "po_outdoor_full_season.avg_annual_yield",
        "Flower_Outdoor": "po_outdoor_full_season.flower_yield_percentage_parse",
        "Smalls_Outdoor": "po_outdoor_full_season.small_yield_percentage_parse",
        "Trim_Outdoor": "po_outdoor_full_season.trim_yield_percentage_parse",
        "Know_your_Cost_per_Sqf_Outdoor": "fd_outdoor_full_season.know_cost_per_sqf_parse",
        "Cost_per_Sqf_Outdoor": "fd_outdoor_full_season.cost_per_sqf_parse",
        "Know_your_Cost_per_Lb_Outdoor": "fd_outdoor_full_season.know_cost_per_lbs_parse",
        "Cost_per_Lb_Outdoor": "fd_outdoor_full_season.cost_per_lbs_parse",
        "Target_Price_Lb_Flower_Outdoor": "fd_outdoor_full_season.tops_target_price_parse",
        "Target_Price_Lb_Smalls_Outdoor": "fd_outdoor_full_season.small_target_price_parse",
        "Target_Price_Lb_Bucked_Untrimmed_Outdoor": "fd_outdoor_full_season.bucked_untrimmed_parse",
        "Target_Price_Lb_Trim_Outdoor": "fd_outdoor_full_season.trim_target_price_parse",
        "Target_Profit_Margin_Outdoor": "fd_outdoor_full_season.target_profit_margin_parse",
        "Harvest_Date_1_Outdoor": "po_outdoor_full_season.cultivars_1_parse",
        #AutoFlower
        "Autoflower": "autoflower_parse",
        "Canopy_Sqf_Outdoor_Autoflower": "outdoor_autoflower.canopy_sqf_parse",
        "Annual_Harvests_Autoflower": "outdoor_autoflower.no_of_harvest_parse",
        "Plants_per_Cycle_Outdoor_Autoflower": "outdoor_autoflower.plants_per_cycle_parse",
        "Yield_Annual_Bucked_Autoflower_Average": "po_outdoor_autoflower.avg_annual_yield",
        "Yield_Plant_Average_Outdoor_Autoflower": "po_outdoor_autoflower.yield_per_plant_parse",
        "Yield_Sqf_Average_Outdoor_Autoflower": "po_outdoor_autoflower.avg_yield_per_sq_ft_parse",
        "Tops_Autoflower": "po_outdoor_autoflower.flower_yield_percentage_parse",
        "Smalls_Autoflower": "po_outdoor_autoflower.small_yield_percentage_parse",
        "Trim_Autoflowers": "po_outdoor_autoflower.trim_yield_percentage_parse",
        "Know_your_Cost_per_Sqf_Autoflower": "fd_outdoor_autoflower.know_cost_per_sqf_parse",
        "Cost_per_Sqf_Autoflower": "fd_outdoor_autoflower.cost_per_sqf_parse",
        "Know_your_Cost_per_Lb_Autoflower": "fd_outdoor_autoflower.know_cost_per_lbs_parse",
        "Cost_per_Lb_Autoflower": "fd_outdoor_autoflower.cost_per_lbs_parse",
        "Target_Price_Lb_Smalls_Autoflower": "fd_outdoor_autoflower.small_target_price_parse",
        "Target_Price_Lb_Tops_Autoflower": "fd_outdoor_autoflower.tops_target_price_parse",
        "Target_Price_Lb_Trim_Autoflower": "fd_outdoor_autoflower.trim_target_price_parse",
        "Target_Price_Lb_Bucked_Autoflower": "fd_outdoor_autoflower.bucked_untrimmed_parse",
        "Target_Profit_Margin_Autoflower": "fd_outdoor_autoflower.target_profit_margin_parse",
        "Harvest_Date_1_Autoflower": "po_outdoor_autoflower.cultivars_1_parse",
        "Harvest_Date_2_Autoflower": "po_outdoor_autoflower.cultivars_2_parse",
        "Harvest_Date_3_Autoflower": "po_outdoor_autoflower.cultivars_3_parse",
        "Harvest_Date_4_Autoflower": "po_outdoor_autoflower.cultivars_4_parse",
        "Harvest_Date_5_Autoflower": "po_outdoor_autoflower.cultivars_5_parse",
        "Harvest_Date_6_Autoflower": "po_outdoor_autoflower.cultivars_6_parse",
        #Indoor
        "Canopy_Sqf_Indoor": "indoor.canopy_sqf_parse",
        "Harvest_Annual_Indoor": "indoor.no_of_harvest_parse",
        "Know_your_Cost_per_Lb_Indoor" :"fd_indoor.know_cost_per_lbs_parse",
        "Cost_per_Lb_Indoor": "fd_indoor.cost_per_lbs_parse",
        "Know_your_Cost_per_Sqf_Indoor": "fd_indoor.know_cost_per_sqf_parse",
        "Cost_per_Sqf_Indoor": "fd_indoor.cost_per_sqf_parse",
        "Target_Price_Lb_Tops_Indoor": "fd_indoor.tops_target_price_parse",
        "Target_Price_Lb_Trim_Indoor": "fd_indoor.trim_target_price_parse",
        "Target_Price_Lb_Smalls": "fd_indoor.small_target_price_parse",
        "Plants_per_Cycle_Indoor": "indoor.plants_per_cycle_parse_parse",
        "Yield_Plant_Average_Indoor": "po_indoor.yield_per_plant_parse",
        "Yield_Sqf_Average_Indoor": "po_indoor.avg_yield_pr_sq_ft_parse",
        "Yield_Annually_Indoor": "po_indoor.avg_annual_yield",
        "Flower_Indoor": "po_indoor.flower_yield_percentage_parse",
        "Smalls_Indoor": "po_indoor.small_yield_percentage_parse",
        "Trim_Indoor": "po_indoor.trim_yield_percentage_parse",
        "Target_Profit_Margin_Indoor": "fd_indoor.target_profit_margin_parse",
        "Harvest_Date_1_Indoor": "po_indoor.cultivars_1_parse",
        "Harvest_Date_2_Indoor": "po_indoor.cultivars_2_parse",
        "Harvest_Date_3_Indoor": "po_indoor.cultivars_3_parse",
        "Harvest_Date_4_Indoor": "po_indoor.cultivars_4_parse",
        "Harvest_Date_5_Indoor": "po_indoor.cultivars_5_parse",
        "Harvest_Date_6_Indoor": "po_indoor.cultivars_6_parse",
        "Harvest_Date_7_Indoor": "po_indoor.cultivars_7_parse",
        "Harvest_Date_8_Indoor": "po_indoor.cultivars_8_parse",
        "Harvest_Date_9_Indoor": "po_indoor.cultivars_9_parse",
        "Harvest_Date_10_Indoor": "po_indoor.cultivars_10_parse",
        "Harvest_Date_11_Indoor": "po_indoor.cultivars_11_parse",
        "Harvest_Date_12_Indoor": "po_indoor.cultivars_12_parse",
        #Financial
        "Yearly_Revenue": "fd_annual_revenue_2019",
        "Yearly_Budget": "fd_yearly_budget",
        #Farm Questionnaire
        "Do_you_work_with_other_Distributors": "other_distributors",
        "Can_you_Process_on_Site": "po_process_on_site",
        "Packaged_Flower_Line": "packaged_flower_line",
        "Farm_Co_Branding_Interest": "interested_in_co_branding",
        "Marketing_material": "marketing_material",
        "Featured_on_our_website_and_social_media": "featured_on_our_site",
        #Other
        "Have_you_ever_had_issues_with_failed_Lab_tests": "issues_with_failed_lab_tests",
        "Yield_Per_Cycle_Mixed_Light": "plants_cultivate_per_cycle",
        "Flower_Target_Price_Lb": "avg_target_price",
        "Bucked_Untrimmed_Target_Price_Lb": "bucked_target_price",
        "Which_third_party_lab_do_you_use": "",
        #Addresses
        "Billing_City": "billing_address.city_parse",
        "Billing_Country": "billing_address.country_parse",
        "Billing_State": "billing_address.state_parse",
        "Billing_Street": "billing_address.street_parse",
        "Billing_Zip_Code": "billing_address.zip_code_parse",
        "Shipping_City": "mailing_address.city_parse",
        "Shipping_Country": "mailing_address.country_parse",
        "Shipping_State": "mailing_address.state_parse",
        "Shipping_Street": "mailing_address.street_parse",
        "Shipping_Zip_Code": "mailing_address.zip_code_parse",
    },
    "Licenses":{
        "id": "license_id",
        "Name": "legal_business_name",
        "Legal_Business_Name": "license_number",
        "License_Type": "license_type",
        "Expiration_Date": "expiration_date",
        "Business_DBA": "",
        "Issue_Date": "issue_date",
        "License_Box_Link": "uploaded_license_to",
        "Premises_Address": "premises_address",
        "Premises_City": "premises_city",
        "Premises_Zipcode": "zip_code",
        "Premises_State": "premises_state",
        "Premises_County": "premises_county",
        "Premises_APN_Number": "premises_apn",
        "Owner": "Owner",
        "Sellers_Permit_Box_Link": "uploaded_sellers_permit_to",
        "W9_Box_Link": "uploaded_w9_to",
    },
    "Accounts":{
        "db_id": "id",
        "Account_Name": "company_name",
        "Website": "website",
        "Client_Code": "",
        "Account_Owner": "",
        "Company_Type": "account_category_parse",
        "Account_Legal_Entity_Name": "",
        "Product_of_Interest": "product_of_interest",
        "Company_Account": "",
        "County": "",
        "Phone": "company_phone",
        "Region": "region",
        "On-boarded_Active_Client": "",
        "Company_Email": "company_email",
        "Dama_Financial_Approved": "",
        "Curator": "",
        "Modified_By": "",
        "Created_By": "",
        "Can_Provide_Transport": "provide_transport",
        "Tag": "",
        "Box_Folder_ID": "",
        "About_Company": "",
        "Created_Time": "",
        "Transportation_Method": "",
        "Modified_Time": "",
        "Last_Activity_Time": "",
        "Currency": "",
        "Shipping_Street": "",
        "Shipping_Remarks": "",
        "Shipping_City": "",
        "Shipping_Code": "",
        "Shipping_State": "",
        "Shipping_Country": "",
        "Account_Image": "",
        "Delivery_Windows": "",
        "Loading_Dock_Location": "",
        "Gate_Code": "",
        "Vehicle_Make_Model": "",
        "Drivers_License_Number": "",
        "Driver_s_Name": "",
        "License_Plate_Number": "",
        "Billing_Company_Name": "billing_compony_name",
        "Preferred_Payment_Method": "preferred_payment",
        "Billing_Street": "billing_street",
        "Bank_Routing_Number": "",
        "Billing_City": "billing_city",
        "Bank_Name": "",
        "Billing_State": "billing_state",
        "Bank_Account_Number": "",
        "Billing_Code": "billing_zip_code",
        "Bank_Street": "",
        "Billing_Country": "",
        "Bank_City": "",
        "Bank_State": "",
        "Bank_Zip_Code": "",
        "Procurement_Rep": "",
        "Logistics_Manager": "logistic_manager_email_parse",
        "Accounting": "",
        "Licenses": "licenses",
        "Seller_s_Permit_Box_Link": "",
        "Verified_License_with_State_Agency": "",
        "Seller_s_Permit_Expiration_Date": "",
        "Date_of_License_Verification": "",
        "Credit_Additional_References": "",
        "Credit_Reference_1_Link": "",
        "Credit_Reference_2_Link": "",
        "Credit_Reference_3_Link": "",
        "LinkedIn": "linked_in",
        "Twitter": "twitter",
        "Facebook": "facebook",
        "Instagram": "instagram",
        "Employees": "",
        "Ownership": "",
        "Ethics_Certifications": "ethics_and_certification",
        "Annual_Revenue": ""
    },
    "Vendors_X_Licenses": {
        "Licenses_Module": "Licenses_Module",
        "Licenses": "Licenses"
    },
    "Accounts_X_Licenses": {
        "Licenses_Module": "Licenses_Module",
        "Licenses": "Licenses"
    },
    "Vendors_X_Cultivars": {
        "Cultivar_Associations": "Cultivar_Associations",
        "Cultivars": "Cultivars"
    },
    "Vendors_To_DB" : {
        "profile_contact":
            {
            "farm_name": "Vendor_Name",
            "vendor_type": "Vendor_Type",
            "about_farm": "About_Company",
            "primary_county": "County",
            "region": "Region",
            "appellation": "Appellations",
            "ethics_and_certifications": "Special_Certifications",
            "other_distributors": "Do_you_work_with_other_Distributors",
            "transportation": "Transportation_Methods",
            "packaged_flower_line": "Packaged_Flower_Line",
            "interested_in_co_branding": "Farm_Co_Branding_Interest",
            "marketing_material": "Marketing_material",
            "featured_on_our_site": "Featured_on_our_website_and_social_media",
            "company_email": "Email",
            "company_phone": "Phone",
            "website": "Website",
            "instagram": "Instagram",
            "facebook": "Facebook",
            "linkedin": "Linkedin",
            "twitter": "Twitter",
            "no_of_employees": "Number_of_Employees",
            "employees": "Contacts_parse"
            },
        "profile_overview": {
            "lighting_type": "Indoor_Mixed_Lighting_Type",
            "type_of_nutrients": "Types_of_Nutrients_Used",
            "interested_in_growing_genetics": "Would_you_grow_genetics_suggested_by_Thrive",
            "issues_with_failed_lab_tests": "Have_you_ever_had_issues_with_failed_Lab_tests",
            "lab_test_issues": "Issues_with_Failed_Lab_Tests",
            "outdoor_full_season.canopy_sqf": "Canopy_Sqf_Outdoor",
            "outdoor_full_season.no_of_harvest": "Annual_Harvest_Outdoor",
            "outdoor_full_season.plants_per_cycle": "Plants_per_Cycle_Outdoor",
            "mixed_light.canopy_sqf": "Total_Canopy_Space",
            "mixed_light.no_of_harvest": "Annual_Harvests",
            "How_many_clones_total_will_you_need_for_the_year": "How_many_clones_total_will_you_need_for_the_year",
            "mixed_light.plants_per_cycle": "Plants_per_Cycle_Mixed_Light",
            "autoflower": "Autoflower",
            "outdoor_autoflower.canopy_sqf": "Canopy_Sqf_Outdoor_Autoflower",
            "outdoor_autoflower.no_of_harvest": "Annual_Harvests_Autoflower",
            "outdoor_autoflower.plants_per_cycle": "Plants_per_Cycle_Outdoor_Autoflower",
            "full_season": "Full_Season",
            "indoor.canopy_sqf": "Canopy_Sqf_Indoor",
            "indoor.no_of_harvest": "Harvest_Annual_Indoor",
            "indoor.plants_per_cycle": "Plants_per_Cycle_Indoor",
            },
        "processing_config":{
            "process_on_site":"Can_you_Process_on_Site",
            "cultivars": "Cultivars",
            "po_mixed_light.cultivars_1": "Harvest_1",
            "po_mixed_light.cultivars_2": "Harvest_2",
            "po_mixed_light.cultivars_3": "Harvest_3",
            "po_mixed_light.cultivars_4": "Harvest_4",
            "po_mixed_light.cultivars_5": "Harvest_5",
            "po_mixed_light.cultivars_6": "Harvest_6",
            "po_mixed_light.cultivars_7": "Harvest_7",
            "po_mixed_light.cultivars_8": "Harvest_8",
            "po_mixed_light.cultivars_9": "Harvest_9",
            "po_mixed_light.cultivars_10": "Harvest_10",
            "po_mixed_light.cultivars_11": "Harvest_11",
            "po_mixed_light.cultivars_12": "Harvest_12",
            "po_outdoor_autoflower.cultivars_1": "Harvest_Date_1_Autoflower",
            "po_outdoor_autoflower.cultivars_2": "Harvest_Date_2_Autoflower",
            "po_outdoor_autoflower.cultivars_3": "Harvest_Date_3_Autoflower",
            "po_outdoor_autoflower.cultivars_4": "Harvest_Date_4_Autoflower",
            "po_outdoor_autoflower.cultivars_5": "Harvest_Date_5_Autoflower",
            "po_outdoor_autoflower.cultivars_6": "Harvest_Date_6_Autoflower",
            "po_indoor.cultivars_1": "Harvest_Date_1_Indoor",
            "po_indoor.cultivars_2": "Harvest_Date_2_Indoor",
            "po_indoor.cultivars_3": "Harvest_Date_3_Indoor",
            "po_indoor.cultivars_4": "Harvest_Date_4_Indoor",
            "po_indoor.cultivars_5": "Harvest_Date_5_Indoor",
            "po_indoor.cultivars_6": "Harvest_Date_6_Indoor",
            "po_indoor.cultivars_7": "Harvest_Date_7_Indoor",
            "po_indoor.cultivars_8": "Harvest_Date_8_Indoor",
            "po_indoor.cultivars_9": "Harvest_Date_9_Indoor",
            "po_indoor.cultivars_10": "Harvest_Date_10_Indoor",
            "po_indoor.cultivars_11": "Harvest_Date_11_Indoor",
            "po_indoor.cultivars_12": "Harvest_Date_12_Indoor",
            "po_outdoor_full_season.cultivars_1": "Harvest_Date_1_Outdoor",
            "po_mixed_light.avg_yield_pr_sq_ft": "Yield_Sqf_Average_Mixed_Light",
            "po_mixed_light.yield_per_plant": "Expected_Yield_Per_Plant",
            "po_mixed_light.flower_yield_percentage": "Flower",
            "po_mixed_light.small_yield_percentage": "Smalls",
            "po_mixed_light.trim_yield_percentage": "Trim",
            "po_outdoor_full_season.avg_yield_pr_sq_ft": "Yield_Sqf_Average_Outdoor",
            "po_outdoor_full_season.yield_per_plant": "Yield_Plant_Average_Outdoor",
            "po_outdoor_full_season.flower_yield_percentage": "Flower_Outdoor",
            "po_outdoor_full_season.small_yield_percentage": "Smalls_Outdoor",
            "po_outdoor_full_season.trim_yield_percentage": "Trim_Outdoor",
            "po_outdoor_autoflower.yield_per_plant": "Yield_Plant_Average_Outdoor_Autoflower",
            "po_outdoor_autoflower.avg_yield_per_sq_ft": "Yield_Sqf_Average_Outdoor_Autoflower",
            "po_outdoor_autoflower.flower_yield_percentage": "Tops_Autoflower",
            "po_outdoor_autoflower.small_yield_percentage": "Smalls_Autoflower",
            "po_outdoor_autoflower.trim_yield_percentage": "Trim_Autoflowers",
            "po_indoor.yield_per_plant": "Yield_Plant_Average_Indoor",
            "po_indoor.avg_yield_pr_sq_ft": "Yield_Sqf_Average_Indoor",
            "po_indoor.flower_yield_percentage": "Flower_Indoor",
            "po_indoor.small_yield_percentage": "Smalls_Indoor",
            "po_indoor.trim_yield_percentage": "Trim_Indoor",
            },
        "financial_details": {
            "fd_annual_revenue_2019": "Yearly_Revenue",
            "fd_yearly_budget": "Yearly_Budget",
            "fd_mixed_light.know_cost_per_sqf": "Know_your_Cost_per_Sqf",
            "fd_mixed_light.cost_per_sqf": "Cost_per_Sqf",
            "fd_mixed_light.know_cost_per_lbs": "Know_your_Cost_per_LB",
            "fd_mixed_light.cost_per_lbs": "Cost_per_LB",
            "fd_mixed_light.tops_target_price": "Flower_Target_Price_Lb",
            "fd_mixed_light.small_target_price": "Smalls_Target_Price_Lb",
            "fd_mixed_light.trim_target_price": "Trim_Target_Price_Lb",
            "fd_mixed_light.bucked_untrimmed": "Bucked_Untrimmed_Target_Price_Lb",
            "fd_mixed_light.target_profit_margin": "Target_Profit_Margin_Mixed_Light",
            "fd_outdoor_full_season.know_cost_per_sqf": "Know_your_Cost_per_Sqf_Outdoor",
            "fd_outdoor_full_season.cost_per_sqf": "Cost_per_Sqf_Outdoor",
            "fd_outdoor_full_season.know_cost_per_lbs": "Know_your_Cost_per_Lb_Outdoor",
            "fd_outdoor_full_season.cost_per_lbs": "Cost_per_Lb_Outdoor",
            "fd_outdoor_full_season.tops_target_price": "Target_Price_Lb_Flower_Outdoor",
            "fd_outdoor_full_season.small_target_price": "Target_Price_Lb_Smalls_Outdoor",
            "fd_outdoor_full_season.bucked_untrimmed": "Target_Price_Lb_Bucked_Untrimmed_Outdoor",
            "fd_outdoor_full_season.trim_target_price": "Target_Price_Lb_Trim_Outdoor",
            "fd_outdoor_full_season.target_profit_margin": "Target_Profit_Margin_Outdoor",
            "fd_outdoor_autoflower.know_cost_per_sqf": "Know_your_Cost_per_Sqf_Autoflower",
            "fd_outdoor_autoflower.cost_per_sqf": "Cost_per_Sqf_Autoflower",
            "fd_outdoor_autoflower.know_cost_per_lbs": "Know_your_Cost_per_Lb_Autoflower",
            "fd_outdoor_autoflower.cost_per_lbs": "Cost_per_Lb_Autoflower",
            "fd_outdoor_autoflower.small_target_price": "Target_Price_Lb_Smalls_Autoflower",
            "fd_outdoor_autoflower.tops_target_price": "Target_Price_Lb_Tops_Autoflower",
            "fd_outdoor_autoflower.trim_target_price": "Target_Price_Lb_Trim_Autoflower",
            "fd_outdoor_autoflower.bucked_untrimmed": "Target_Price_Lb_Bucked_Autoflower",
            "fd_outdoor_autoflower.target_profit_margin": "Target_Profit_Margin_Autoflower",
            "fd_indoor.know_cost_per_lbs": "Know_your_Cost_per_Lb_Indoor",
            "fd_indoor.cost_per_lbs": "Cost_per_Lb_Indoor",
            "fd_indoor.know_cost_per_sqf": "Know_your_Cost_per_Sqf_Indoor",
            "fd_indoor.cost_per_sqf": "Cost_per_Sqf_Indoor",
            "fd_indoor.tops_target_price": "Target_Price_Lb_Tops_Indoor",
            "fd_indoor.trim_target_price": "Target_Price_Lb_Trim_Indoor",
            "fd_indoor.small_target_price": "Target_Price_Lb_Smalls",
            "fd_indoor.target_profit_margin": "Target_Profit_Margin_Indoor"
        }
    },
    "Licenses_To_DB": {
            "license_id": "id",
            "license_number": "Legal_Business_Name",
            "legal_business_name": "Name",
            "license_type": "License_Type",
            "expiration_date": "Expiration_Date",
            "business_dba": "Business_DBA",
            "issue_date": "Issue_Date",
            "uploaded_license_to": "License_Box_Link",
            "uploaded_w9_to": "W9_Box_Link",
            "premises_address": "Premises_Address",
            "premises_city": "Premises_City",
            "zip_code": "Premises_Zipcode",
            "premises_state": "Premises_State",
            "premises_county": "Premises_County",
            "premises_apn": "Premises_APN_Number",
            "Owner": "Owner",
            "uploaded_sellers_permit_to": "Sellers_Permit_Box_Link",
            },
    "Accounts_To_DB":
        {
            "basic_profile":
                {
                    "company_name": "Account_Name",
                    "company_type": "Company_Type",
                    "region": "Region",
                    "preferred_payment": "Preferred_Payment_Method",
                    "cultivars_of_interest": "",
                    "ethics_and_certification": "Ethics_Certifications",
                    "product_of_interest": "Product_of_Interest",
                    "provide_transport": "Can_Provide_Transport",
                    },
            "contact_info":
                {
                    "company_phone": "Phone",
                    "website": "Website",
                    "company_email": "Company_Email",
                    "owner_name": "",
                    "owner_email": "",
                    "owner_phone": "",
                    "logistic_manager_name": "Logistics_Manager",
                    "logistic_manager_email": "Logistics_Manager",
                    "logistic_manager_phone": "Logistics_Manager",
                    "instagram": "Instagram",
                    "linked_in": "LinkedIn",
                    "twitter": "Twitter",
                    "facebook": "Facebook",
                    "billing_compony_name": "Billing_Company_Name",
                    "billing_street": "Billing_Street",
                    "billing_street_line_2": "",
                    "billing_city": "Billing_City",
                    "billing_zip_code": "Billing_Code",
                    "billing_state": "Billing_State",
                }
        },
    "Leads":
        {
            "Layout": 'layout_parse',
            "Layout_Name": "Layout_Name",
            "Company": "Company",
            "Last_Name": "last_name",
            "Company_Name": "company_name",
            "First_Name": "first_name",
            "Lead_Source": "heard_from",
            "Owner": "Owner",
            "Company_Type": "Company_Type",
            "Legal_Entity_Name": "Legal_Entity_Name",
            "Email": "email",
            "Phone": "Phone",
            "Designation": "Designation",
            "Mobile": "Mobile",
            "Lead_Status": "Lead_Status",
            "Cultivation_Type": "Cultivation_Type",
            "County": "County",
            "Vendor_Type": "vendor_category",
            "Products_of_Interest": "Products_of_Interest",
            "Associated_License": "Associated_License",
            "Created_By": "Created_By",
            "IFP_Status": "IFP_Status",
            "Region": "Region",
            "Modified_By": "Modified_By",
            "Annual_Revenue": "Annual_Revenue",
            "No_of_Employees": "No_of_Employees",
            "Layout": "Layout",
            "Website": "Website",
            "Tag": "Tag",
            "Email_Opt_Out": "Email_Opt_Out",
            "box__Box_Folder_ID": "box__Box_Folder_ID",
            "Created_Time": "Created_Time",
            "Description": "message",
            "Modified_Time": "Modified_Time",
            "Industry": "Industry",
            "Last_Activity_Time": "Last_Activity_Time",
            "Client_Transportation_Options": "Client_Transportation_Options",
            "Converted_Date_Time": "Converted_Date_Time",
            "Is_Record_Duplicate": "Is_Record_Duplicate",
            "Currency": "Currency",
            "City": "City",
            "Mailing_Street": "Mailing_Street",
            "Mailing_State": "Mailing_State",
            "Street": "Street",
            "Mailing_City": "Mailing_City",
            "Mailing_Country": "Mailing_Country",
            "Zip_Code": "Zip_Code",
            "Mailing_Zip_Code": "Mailing_Zip_Code",
            "State": "State",
            "Country": "Country",
            "Record_Image": "Record_Image",
            "Salutation": "Salutation",
            "Canopy_Size": "Canopy_Size",
            "Annual_Production_Lbs": "Annual_Production_Lbs",
            "LinkedIn": "LinkedIn",
            "Full_Name": "Full_Name",
            "Canopy_Sqf_Outdoor": "Canopy_Sqf_Outdoor",
            "Type_of_Nutrients_Used": "Type_of_Nutrients_Used",
            "Instagram": "Instagram",
            "Canopy_Sqf_Indoor": "Canopy_Sqf_Indoor",
            "Indoor_Mixed_Lighting_Type": "Indoor_Mixed_Lighting_Type",
            "Facebook": "Facebook",
            "Twitter": "Twitter",
            "Secondary_Email": "Secondary_Email",
            "Billing_Street": "Billing_Street",
            "Billing_State": "Billing_State",
            "Billing_City": "Billing_City",
            "Billing_Country": "Billing_Country",
            "Billing_Zip_Code": "Billing_Zip_Code",
            "Vehicle_Make_Model": "Vehicle_Make_Model",
            "Drivers_License_Number": "Drivers_License_Number",
            "Name_of_Driver": "Name_of_Driver",
            "License_Plate_Number": "License_Plate_Number",
            "Annual_Revenue_Estimate": "Annual_Revenue_Estimate",
            "Average_Time_Spent_Minutes": "Average_Time_Spent_Minutes",
            "Canopy_Acres_Indoor": "Canopy_Acres_Indoor",
            "Canopy_Mixed_Light_Acres": "Canopy_Mixed_Light_Acres",
            "Canopy_Acres_Outdoor": "Canopy_Acres_Outdoor",
            "Canopy_Sqf_Indoor": "Canopy_Sqf_Indoor",
            "Canopy_Size": "Canopy_Size",
            "Canopy_Sqf_Outdoor": "Canopy_Sqf_Outdoor",
            "Chemicals_and_Reagents": "Chemicals_and_Reagents",
            "Chilling_Equipment": "Chilling_Equipment",
            "Days_Visited": "Days_Visited",
            "Drying": "Drying",
            "Ethics_Certifications": "Ethics_Certifications",
            "First_Visited_URL": "First_Visited_URL",
            "First_Visited_Time": "First_Visited_Time",
            "Greenhouses": "Greenhouses",
            "IFP_Services_Provided": "IFP_Services_Provided",
            "Irrigation_and_Plumbing": "Irrigation_and_Plumbing",
            "Janitorial_Sanitation": "Janitorial_Sanitation",
            "Lab_Equipment": "Lab_Equipment",
            "Whale": "Whale",
            "Lighting": "Lighting",
            "Last_Visited_Time": "Last_Visited_Time",
            "Motors_and_Pumps": "Motors_and_Pumps",
            "Number_Of_Chats": "Number_Of_Chats",
            "Nutrients_Amendments": "Nutrients_Amendments",
            "Pesticides_Herbicides_and_Fungicides": "Pesticides_Herbicides_and_Fungicides",
            "PPE": "PPE",
            "Prediction_Score": "Prediction_Score",
            "Product_Storage": "Product_Storage",
            "Referrer": "Referrer",
            "Revenue_Mixed_Light_Smalls": "Revenue_Mixed_Light_Smalls",
            "Revenue_Mixed_Light_Tops": "Revenue_Mixed_Light_Tops",
            "Revenue_Mixed_Light_Trim": "Revenue_Mixed_Light_Trim",
            "Show_Internal_Information": "Show_Internal_Information",
            "Sprayers_Applicators": "Sprayers_Applicators",
            "Trim_Equipment": "Trim_Equipment",
            "Vendor_Product_s_Categories": "Vendor_Product_s_Categories",
            "Vendor_Service_s_Categories": "Vendor_Service_s_Categories",
            "Visitor_Score": "Visitor_Score",
            "Yield_lbs_Mixed_Light_Bucked_Untrimmed": "Yield_lbs_Mixed_Light_Bucked_Untrimmed",
            "Yield_lbs_Mixed_Light_Smalls": "Yield_lbs_Mixed_Light_Smalls",
            "Mixed_Light_Tops_Estimate": "Mixed_Light_Tops_Estimate",
            "Yield_lbs_Mixed_Light_Trim": "Yield_lbs_Mixed_Light_Trim",
            "Yield_lbs_Outdoor_Bucked_Forecast": "Yield_lbs_Outdoor_Bucked_Forecast",
            "Yield_lbs_Outdoor_Smalls": "Yield_lbs_Outdoor_Smalls",
            "Yield_lbs_Outdoor_Tops": "Yield_lbs_Outdoor_Tops",
            "Yield_lbs_Outdoor_Trim": "Yield_lbs_Outdoor_Trim",
        },
    "Cultivars":
        {
            "Description": "description",
            "Effects": "effect",
            "Name": "cultivar_name",
            "CBD_Range": "cbd_range",
            "Record_Image": "cultivar_image",
            "THCv_Range": "thcv_range",
            "Modified_By": "modified_by_parse",
            "Terpenes_Secondary": "terpenes_secondary",
            "Parent_2": "parent_2_parse",
            "Parent_1": "parent_1_parse",
            "id": "cultivar_crm_id",
            "Modified_Time": "modify_time",
            "Created_Time": "create_time",
            "Flavor": "flavor",
            "Type": "cultivar_type",
            "THC_Range": "thc_range",
            "CBG_Range": "cbg_range",
            "Created_By": "created_by_parse",
            "Terpenes": "terpenes_primary"
        },
}

LAYOUTS = {
    "Leads":
        {
            "accounts": "4230236000001156737",
            "vendor_cannabis_cultivar": "4230236000001229441",
            "vendor_cannabis_non_cultivator": "4230236000001229442",
            "vendor_non_cannabis": "4230236000001229443",
        },
}

VENDOR_TYPES = {
    "cultivation": "Cultivator",
    "nursery": "Nursery",
    "manufacturing": "Manufacturer",
    "distribution": "Distributor",
    "retail": "Retailer",
    "processing": "Processor",
    "testing": "Testing",
    "event": "Event",
    "brand": "Brand",
    "hemp": "Hemp",
    "ancillary products": "Ancillary Products",
    "ancillary services": "Ancillary Services",
    "investment": "Investor",
    "patient": "Patient",
    "healthcare": "Healthcare"
}

# Display value : Actual Value
# ACCOUNT_TYPES = {
#  "Ancillary Products": "Vendor - Equipment and Supplies",
#  "Ancillary Services": "Professional Services",
#  "Brand - Concentrates": "Brand",
#  "Brand - Edibles": "Edibles",
#  "Brand - Flower": "Flower Brand",
#  "Brand - Vape Pens": "Vape Pens",
#  "Cultivation": "Cultivator",
#  "Delivery": "Delivery",
#  "Distribution": "Distributor",
#  "Hemp": "Hemp",
#  "Investment": "Investor",
#  "Legal": "Legal",
#  "Lending": "Lender",
#  "Manufacturing": "Manufacturing - Type 6",
#  "Marketing": "Marketing",
#  "Nursery": "Nursery",
#  "Processing": "Processing",
#  "Retail": "Retail",
#  "Transportation": "Transport"}

ACCOUNT_TYPES = {
    "cultivator":"Cultivator",
}


