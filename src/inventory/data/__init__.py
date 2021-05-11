

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


ORG_ITEM_CUSTOM_FIELD_MAP = (
    # Thrive Society (EFD LLC)          Eco Farm Labs (EFL LLC)             Eco Farm Nursery (EFN LLC)
    ('cf_farm_price_2',                 'cf_farm_price',                    'cf_farm_price_pretax'),
    ('cf_cfi_published',                'cf_cfi_published',                 'cf_publish_to_cfi'),
    ('cf_status',                       'cf_status',                        'cf_status'),
    ('cf_vendor_name',                  'cf_vendor_name',                   'cf_vendor'),
    ('cf_client_code',                  'cf_client_code',                   'cf_client_code'),
    ('cf_strain_name',                  'cf_strain_name',                   ''),
    ('cf_cultivar_type',                'cf_cultivar_type',                 'cf_cultivar_type'),
    ('cf_cannabis_grade_and_category',  'cf_cannabis_grade_and_category',   ''),
    ('cf_grade_seller',                 '',                                 ''),
    ('cf_lab_test_sample_id',           '',                                 ''),
    ('cf_sample_in_house',              '',                                 ''),
    ('cf_seller_position',              'cf_lpn',                           ''),
    ('cf_marge_per_unit',               '',                                 ''),
    ('cf_gross_margin_per_unit',        '',                                 ''),
    ('cf_total_margin_per_item',        '',                                 ''),
    ('cf_procurement_rep',              '',                                 ''),
    ('cf_payment_terms',                '',                                 'cf_payment_terms'),
    ('cf_minimum_quantity',             '',                                 'cf_minimum_quantity'),
    ('cf_received_date',                'cf_received_date',                 ''),
    ('cf_quantity_estimate',            '',                                 'cf_quantity_estimate'),
    ('cf_next_harvest_date',            ''                       ,          ''),
    ('cf_date_available',               '',                                 ''),
    ('cf_metrc_source_package_id',      'cf_metrc_source_package_id',       'cf_metrc_source_package_id'),
    ('cf_harvest_date',                 '',                                 ''),
    ('cf_market_feedback',              '',                                 ''),
    ('cf_available_date',               '',                                 'cf_available_date'),
    ('cf_price_change',                 '',                                 ''),
    ('cf_price_change_date',            '',                                 ''),
    ('cf_payment_method',               '',                                 ''),
    ('cf_batch_quality_notes',          'cf_batch_notes',                   'cf_batch_quality_notes'),
    ('cf_lab_testing_services',         '',                                 ''),
    ('cf_flower_smalls',                '',                                 ''),
    ('cf_sample_lbs_inlcuded_in_eob_',  '',                                 ''),
    ('cf_lpn',                          '',                                 ''),

    ('',                                'cf_lab_testing_status',            ''),
    ('',                                'cf_manufacturing_date',            ''),
    ('',                                'cf_batch_blending',                ''),
    ('',                                'cf_lab_test_results_box_url',      ''),
    ('',                                'cf_administrative_hold',           ''),
    ('',                                'cf_qa_intake_grading_sheet_id',    ''),
    ('',                                'cf_cultivar_name',                 'cf_cultivar_name'),
    ('',                                '',                                 'cf_flowering_period'),
    ('',                                '',                                 'cf_clone_date'),
    ('',                                '',                                 'cf_lab_sample_id'),
    ('',                                '',                                 'cf_order_type'),
    ('',                                '',                                 'cf_order_type'),
    ('',                                '',                                 'cf_rooting_time'),
    ('',                                '',                                 ''),
)

ITEM_CUSTOM_FIELD_MAP_EFD_TO_EFL = {x[0]: x[1] for x in ORG_ITEM_CUSTOM_FIELD_MAP if x[0]}
ITEM_CUSTOM_FIELD_MAP_EFD_TO_EFN = {x[0]: x[2] for x in ORG_ITEM_CUSTOM_FIELD_MAP if x[0]}