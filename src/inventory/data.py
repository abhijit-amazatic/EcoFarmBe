

CUSTOM_INVENTORY_ITEM_DEFAULT_ACCOUNTS = {
    '709199483':{   # Test Books Organization
        'account_id':           '2185756000001423419', # '3rd Party Flower Sales'
        'purchase_account_id':  '2185756000001031365', # 'Product Costs - Flower'
        'inventory_account_id': '2185756000001423111', # 'Inventory - In the Field'
    },
    '708284623': {   # Thrive Society (EFD LLC)
        'account_id':           '2155380000000448337', # '3rd Party Flower Sales'
        'purchase_account_id':  '2155380000000565567', # 'Product Costs - Flower'
        'inventory_account_id': '2155380000000448361', # 'Inventory - In the Field'
    },
    '708285820': {   # Eco Farm Labs (EFL LLC)
        'account_id':           '2168475000000225856', # '3rd Party Flower Sales'
        'purchase_account_id':  '2168475000000225908', # 'Product Costs - Flower'
        # 'inventory_account_id': '', # 'Inventory - In the Field'
    },
    '708301606': {   # Eco Farm Nursery (EFN LLC)
        'account_id':           '2158711000001027029', # 'Product Sales - Clones'
        'purchase_account_id':  '2158711000001027033', # 'Product Costs - Clones'
        'inventory_account_id': '2158711000000198057', # 'Inventory - Clones'
    },
}


ORG_ITEM_CUSTOM_FIELD_MAP_TABLE = (
    # maping_field                     Thrive Society (EFD LLC)          Eco Farm Labs (EFL LLC)           Eco Farm Nursery (EFN LLC)
    ('cf_flower_smalls',               'cf_flower_smalls',               '',                               '',                          ),
    ('cf_farm_price_2',                'cf_farm_price_2',                'cf_farm_price',                  'cf_farm_price_pretax',      ),
    ('cf_cfi_published',               'cf_cfi_published',               'cf_cfi_published',               'cf_publish_to_cfi',         ),
    ('cf_status',                      'cf_status',                      'cf_status',                      'cf_status',                 ),
    ('cf_vendor_name',                 'cf_vendor_name',                 'cf_vendor_name',                 'cf_vendor',                 ),
    ('cf_client_code',                 'cf_client_code',                 'cf_client_code',                 'cf_client_code',            ),
    ('cf_cultivation_type',            'cf_cultivation_type',            '',                               '',                          ),
    ('cf_strain_name',                 'cf_strain_name',                 'cf_cultivar_name',               'cf_cultivar_name',          ),
    ('cf_cultivar_type',               'cf_cultivar_type',               'cf_cultivar_type',               'cf_cultivar_type',          ),
    ('cf_tags',                        'cf_tags',                        '',                               'cf_tags',                   ),
    ('cf_cannabis_grade_and_category', 'cf_cannabis_grade_and_category', 'cf_cannabis_grade_and_category', '',                          ),
    ('cf_grade_seller',                'cf_grade_seller',                '',                               '',                          ),
    ('cf_lab_test_sample_id',          'cf_lab_test_sample_id',          '',                               'cf_lab_sample_id',          ),
    ('cf_sample_in_house',             'cf_sample_in_house',             '',                               '',                          ),
    ('cf_seller_position',             'cf_seller_position',             '',                               '',                          ),
    ('cf_ifp_farm',                    'cf_ifp_farm',                    '',                               '',                          ), # inactive
    ('cf_marge_per_unit',              'cf_marge_per_unit',              '',                               '',                          ),
    ('cf_gross_margin_per_unit',       'cf_gross_margin_per_unit',       '',                               '',                          ),
    ('cf_total_margin_per_item',       'cf_total_margin_per_item',       '',                               '',                          ),
    ('cf_procurement_rep',             'cf_procurement_rep',             '',                               '',                          ),
    ('cf_payment_terms',               'cf_payment_terms',               '',                               'cf_payment_terms',          ),
    ('cf_minimum_quantity',            'cf_minimum_quantity',            '',                               '',                          ),
    ('cf_received_date',               'cf_received_date',               'cf_received_date',               '',                          ),
    ('cf_quantity_estimate',           'cf_quantity_estimate',           '',                               'cf_quantity_estimate',      ),
    ('cf_next_harvest_date',           'cf_next_harvest_date',           '',                               '',                          ),
    ('cf_date_available',              'cf_date_available',              'cf_availability_date',           'cf_available_date',         ),
    ('cf_metrc_source_package_id',     'cf_metrc_source_package_id',     '',                               '',                          ),
    ('cf_harvest_date',                'cf_harvest_date',                '',                               '',                          ),
    ('cf_market_feedback',             'cf_market_feedback',             '',                               '',                          ), # inactive
    ('cf_available_date',              'cf_available_date',              '',                               '',                          ),
    ('cf_offer_price',                 'cf_offer_price',                 '',                               '',                          ), # inactive
    ('cf_price_change',                'cf_price_change',                '',                               '',                          ), # inactive
    ('cf_price_change_date',           'cf_price_change_date',           '',                               '',                          ), # inactive
    ('cf_payment_method',              'cf_payment_method',              '',                               '',                          ),
    ('cf_batch_quality_notes',         'cf_batch_quality_notes',         'cf_batch_notes',                 'cf_batch_quality_notes',    ),
    ('cf_lab_testing_services',        'cf_lab_testing_services',        '',                               '',                          ),
    ('cf_sample_lbs_inlcuded_in_eob_', 'cf_sample_lbs_inlcuded_in_eob_', '',                               '',                          ),
    ('cf_lpn',                         'cf_lpn',                         'cf_lpn',                         '',                          ),
    ('cf_trim_qty_lbs',                'cf_trim_qty_lbs',                'cf_trim_qty_lbs',                '',                          ),
    ('cf_batch_qty_g',                 'cf_batch_qty_g',                 'cf_batch_qty_g',                 '',                          ),
    ('cf_client_id',                   'cf_client_id',                   'cf_client_id',                   'cf_client_id',              ),
    ('cf_cannabinoid_percentage',      'cf_cannabinoid_percentage',      'cf_cannabinoid_percentage',      '',                          ),
    ('cf_cannabinoid_type',            'cf_cannabinoid_type',            'cf_cannabinoid_type',            '',                          ),
    ('cf_manufacturing_date',          '',                               'cf_manufacturing_date',          '',                          ),
    ('cf_lab_testing_status',          '',                               'cf_lab_testing_status',          '',                          ),
    ('cf_r_d_test_id_number',          '',                               'cf_r_d_test_id_number',          '',                          ),
    ('cf_qa_intake_grading_sheet_id',  '',                               'cf_qa_intake_grading_sheet_id',  '',                          ),
    ('cf_administrative_hold',         '',                               'cf_administrative_hold',         '',                          ),
    ('cf_batch_blending',              '',                               'cf_batch_blending',              '',                          ),
    ('cf_lab_test_results_box_url',    '',                               'cf_lab_test_results_box_url',    '',                          ),
    ('cf_metrc_source_package_id',     '',                               'cf_metrc_source_package_id',     '',                          ),
    ('cf_flowering_period',            '',                               '',                               'cf_flowering_period',       ),
    ('cf_minimum_quantity',            '',                               '',                               'cf_minimum_quantity',       ),
    ('cf_rooting_time',                '',                               '',                               'cf_rooting_time',           ),
    ('cf_clone_date',                  '',                               '',                               'cf_clone_date',             ),
    ('cf_metrc_source_package_id',     '',                               '',                               'cf_metrc_source_package_id',),
    ('cf_order_type',                  '',                               '',                               'cf_order_type',             ),
    ('cf_clone_size_in',               '',                               '',                               'cf_clone_size_in',          ),
    # ('',                               '',                              '',                                ''                           ),
)


ITEM_CUSTOM_FIELD_ORG_MAP = {
    'efd': { x[0]: x[1] for x in ORG_ITEM_CUSTOM_FIELD_MAP_TABLE if x[1] },
    'efl': { x[0]: x[2] for x in ORG_ITEM_CUSTOM_FIELD_MAP_TABLE if x[2] },
    'efn': { x[0]: x[3] for x in ORG_ITEM_CUSTOM_FIELD_MAP_TABLE if x[3] },
}



CATEGORY_GROUP_MAP = {
    'Flowers': (
        'Wholesale - Flower',
        'Flower',
        'In the Field',
        'Flower - Tops',
        'Tops',
        'Flower - Bucked Untrimmed',
        'Flower - Bucked Untrimmed - Seeded',
        'Flower - Bucked Untrimmed - Contaminated',
        'Flower - Small',
    ),
    'Trims': (
        'Trim',
        'Trim - CBD',
        'Trim - THC',
    ),
    'Kief': (
        'Kief',
    ),
    # 'Packaged Goods',
    'Concentrates': (
        'Wholesale - Concentrates'
        'Crude Oil',
        'Crude Oil - THC',
        'Crude Oil - CBD',
        'Shatter',
        'Sauce',
        'Crumble',
    ),
    'Distillates': (
        'Distillate Oil',
        'Distillate Oil - CBD',
        'Distillate Oil - THC',
        'Distillate Oil - THC - First Pass',
        'Distillate Oil - THC - Second Pass',
    ),
    'Isolates': (
        'Isolates',
        'Isolates - CBD',
        'Isolates - THC',
        'Isolates - CBG',
        'Isolates - CBN',
    ),
    'Terpenes': (
        'Terpenes',
        'Terpenes - Cultivar Specific',
        'Terpenes - Cultivar Blended',
    ),
    # 'Lab Testing',
    # 'Services',
    # 'QC',
    # 'Transport',
    # 'Secure Cash Handling',
    'Clones': (
        'Clones',
    ),
    # 'tmp': (
    #     'Jars 1/8',
    #     'Mylar  1/8',
    #     'Lab Testing',
    #     'QC',
    #     'Secure Cash Handling',
    #     'Services',
    #     'Transport',
    # )
}

CG = {cat: k for k, v in CATEGORY_GROUP_MAP.items() for cat in v}



_CATEGORY_CANNABINOID_TYPE_MAP = {
    'THC': (
        'Crude Oil - THC',
        'Distillate Oil - THC',
        'Distillate Oil - THC - First Pass',
        'Distillate Oil - THC - Second Pass',
        'Isolates - THC',
    ),
    'CBD': (
        'Crude Oil - CBD',
        'Distillate Oil - CBD',
        'Isolates - CBD',
    ),
    'CBG': (
        'Isolates - CBG',
    ),
    'CBN': (
        'Isolates - CBN',
    ),
}

CATEGORY_CANNABINOID_TYPE_MAP = {cat: k for k, v in _CATEGORY_CANNABINOID_TYPE_MAP.items() for cat in v}

ITEM_CATEGORY_UNIT_MAP = {
    'Flowers':      'lb',
    'Trims':        'lb',
    'Kief':         'g',
    'Isolates':     'g',
    'Distillates':  'g',
    'Concentrates': 'g',
    'Terpenes':     'g',
    'Clones':       'pcs',
}
