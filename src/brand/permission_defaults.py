role_map = {
    "License Owner": "license_owner",
    "Farm Manager": "farm_manager",
    "Sales/Inventory": "sales_or_inventory",
    "Logistics": "logistics",
    "Billing": "billing",
    "Owner": "owner",
}


DEFAULT_ROLE_PERM = {
    'License Owner': [
        "view_license",
        "edit_license",
        "view_license_profile",
        "edit_license_profile",
    ],
    'Farm Manager': [
        "view_cultivation_overview",
        "add_cultivation_overview",
        "edit_cultivation_overview",
        "delete_cultivation_overview",
        "view_crop_overview",
        "add_crop_overview",
        "edit_crop_overview",
        "delete_crop_overview",
    ],
    'Sales/Inventory': [
        "view_sales",
        "view_inventory",
        "add_inventory",
        "edit_inventory",
    ],
    'Billing': [
        "view_profile_contact",
        "add_profile_contact",
        "edit_profile_contact",
        "delete_profile_contact",
        "view_billing_information",
        "edit_billing_information",
        "view_billing_address",
        "edit_billing_address",
        "view_shipping_address",
        "edit_shipping_address",
        "view_mailing_address",
        "edit_mailing_address",
        "view_program_overview",
    ],
    'Logistics': [
        "view_license",
        "view_brand",
        "view_license_profile",
    ]
}

SALES_REP_GROUP_NAME = 'Sales Rep'

SALES_REP_PERM = [
    'view_billing_address',
    'edit_billing_address',
    'view_mailing_address',
    'edit_mailing_address',
    'view_shipping_address',
    'edit_shipping_address',
    'add_license',
    'delete_license',
    'edit_license',
    'view_license',
    'view_inventory',
    'view_sales',
    'add_brand',
    # 'add_organization',
    # 'add_organization_role',
    # 'add_organization_user_role',
    # 'delete_brand',
    # 'delete_organization',
    # 'delete_organization_role',
    # 'delete_organization_user',
    # 'delete_organization_user_role',
    'edit_brand',
    # 'edit_organization',
    # 'edit_organization_role',
    # 'edit_organization_user',
    # 'edit_organization_user_role',
    # 'invite_user_to_organization',
    'view_brand',
    'view_organization',
    'view_organization_role',
    'view_organization_user',
    'view_organization_user_role',
    # 'add_crop_overview',
    # 'add_cultivation_overview',
    # 'add_financial_overview',
    # 'add_profile_contact',
    # 'add_program_overview',
    # 'delete_crop_overview',
    # 'delete_cultivation_overview',
    # 'delete_financial_overview',
    # 'delete_profile_contact',
    # 'delete_program_overview',
    # 'edit_crop_overview',
    # 'edit_cultivation_overview',
    'edit_financial_overview',
    'edit_license_profile',
    # 'edit_profile_contact',
    # 'edit_program_overview',
    'view_crop_overview',
    'view_cultivation_overview',
    'view_financial_overview',
    'view_license_profile',
    'view_profile_contact',
    'view_program_overview'
]
