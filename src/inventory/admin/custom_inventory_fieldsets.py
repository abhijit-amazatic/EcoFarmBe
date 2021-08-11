fieldsets_default = {
    None: {
        'fields': (
            'zoho_organization',
            'cultivar',
            # 'cultivar_name',
            'category_name',
            'marketplace_status',
        ),
    },
    'BATCH & QUALITY INFORMATION': {
        'fields': (
            'cultivation_type',
            'quantity_available',
            ('trim_used', 'trim_used_doc'),
            'trim_used_verified',
            'harvest_date',
            'need_lab_testing_service',
            'batch_availability_date',
            'grade_estimate',
            'product_quality_notes',
        ),
    },
    'PRICING INFORMATION': {
        'fields': (
            'farm_ask_price',
            'pricing_position',
            # 'have_minimum_order_quantity',
            # 'minimum_order_quantity',
            'payment_terms',
            'payment_method',
        ),
    },
    'SAMPLE LOGISTICS (PICKUP OR DROP OFF)': {
        'fields': (
            'transportation',
            'best_contact_Day_of_week',
            'best_contact_time_from',
            'best_contact_time_to',
        ),
    },
    'Extra Info': {
        'fields': (
            'status',
            'license_profile',
            'vendor_name',
            'crm_vendor_id',
            'client_code',
            'procurement_rep',
            'zoho_item_id',
            'sku',
            'po_id',
            'po_number',
            'approved_by',
            'approved_on',
            'created_by',
            'created_on',
            'updated_on',
        ),
    },
}


_fieldsets = {
    'default': {
        **fieldsets_default,
    },
    'Flowers': {
        **fieldsets_default,
        'BATCH & QUALITY INFORMATION': {
            'fields': (
                'cultivation_type',
                'quantity_available',
                'batch_availability_date',
                'harvest_date',
                'grade_estimate',
                'product_quality_notes',
                'need_lab_testing_service',
            ),
        },
    },
    'Trims': {
        **fieldsets_default,
        'BATCH & QUALITY INFORMATION': {
            'fields': (
                'cultivation_type',
                'quantity_available',
                'harvest_date',
                'batch_availability_date',
                'grade_estimate',
                'product_quality_notes',
                'need_lab_testing_service',
            ),
        },
    },
    'Concentrates': {
        **fieldsets_default,
        'BATCH & QUALITY INFORMATION': {
            'fields': (
                'quantity_available',
                'total_batch_quantity',
                ('trim_used', 'trim_used_doc'),
                'trim_used_verified',
                'manufacturing_date',
                'batch_availability_date',
                'product_quality_notes',
                'need_lab_testing_service',
            ),
        },
    },
    'Isolates': {
        **fieldsets_default,
        'BATCH & QUALITY INFORMATION': {
            'fields': (
                'quantity_available',
                'total_batch_quantity',
                ('trim_used', 'trim_used_doc'),
                'trim_used_verified',
                'manufacturing_date',
                'batch_availability_date',
                'grade_estimate',
                'product_quality_notes',
                'need_lab_testing_service',
            ),
        },
    },
    'Terpenes': {
        **fieldsets_default,
        'BATCH & QUALITY INFORMATION': {
            'fields': (
                'quantity_available',
                'total_batch_quantity',
                ('trim_used', 'trim_used_doc'),
                'trim_used_verified',
                'manufacturing_date',
                'batch_availability_date',
                'grade_estimate',
                'product_quality_notes',
                'need_lab_testing_service',
            ),
        },
    },
    'Clones': {
        **fieldsets_default,
        'BATCH & QUALITY INFORMATION': {
            'fields': (
                'clone_size',
                'quantity_available',
                'days_to_prepare_clones',
                'product_quality_notes',
            ),
        },
    },
}



fieldsets = {fsk: tuple((k, v) for k, v in fsv.items()) for fsk, fsv in _fieldsets.items()}