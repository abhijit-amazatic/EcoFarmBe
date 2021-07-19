BOOKS_FORMAT_DICT = {
    "sales_order": {
        'salesorder_id': 'salesorder_id',
        'documents': 'documents',
        'salesorder_number': 'salesorder_number',
        'status': 'status',
        'color_code': 'color_code',
        'current_sub_status_id': 'current_sub_status_id',
        'current_sub_status': 'current_sub_status',
        'sub_statuses': 'sub_statuses',
        'shipment_date': 'shipment_date',
        'reference_number': 'reference_number',
        'customer_id': 'customer_id',
        'customer_name': 'customer_name',
        'contact_persons': 'contact_persons',
        'contact_person_details': 'contact_person_details',
        'contact_category': 'contact_category',
        'currency_id': 'currency_id',
        'currency_code': 'currency_code',
        'currency_symbol': 'currency_symbol',
        'exchange_rate': 'exchange_rate',
        'discount_amount': 'discount_amount',
        'discount': 'discount',
        'discount_applied_on_amount': 'discount_applied_on_amount',
        'is_discount_before_tax': 'is_discount_before_tax',
        'discount_type': 'discount_type',
        'estimate_id': 'estimate_id',
        'delivery_method': 'delivery_method',
        'delivery_method_id': 'delivery_method_id',
        'is_inclusive_tax': 'is_inclusive_tax',
        'order_status': 'order_status',
        'invoiced_status': 'invoiced_status',
        'account_identifier': 'account_identifier',
        'integration_id': 'integration_id',
        'has_qty_cancelled': 'has_qty_cancelled',
        'is_offline_payment': 'is_offline_payment',
        'created_by_email': 'created_by_email',
        'line_items': 'line_items',
        'submitter_id': 'submitter_id',
        'approver_id': 'approver_id',
        'submitted_date': 'submitted_date',
        'submitted_by': 'submitted_by',
        'shipping_charge': 'shipping_charge',
        'bcy_shipping_charge': 'bcy_shipping_charge',
        'adjustment': 'adjustment',
        'bcy_adjustment': 'bcy_adjustment',
        'adjustment_description': 'adjustment_description',
        'roundoff_value': 'roundoff_value',
        'transaction_rounding_type': 'transaction_rounding_type',
        'sub_total': 'sub_total',
        'bcy_sub_total': 'bcy_sub_total',
        'sub_total_inclusive_of_tax': 'sub_total_inclusive_of_tax',
        'sub_total_exclusive_of_discount': 'sub_total_exclusive_of_discount',
        'discount_total': 'discount_total',
        'bcy_discount_total': 'bcy_discount_total',
        'discount_percent': 'discount_percent',
        'tax_total': 'tax_total',
        'bcy_tax_total': 'bcy_tax_total',
        'total': 'total',
        'bcy_total': 'bcy_total',
        'taxes': 'taxes',
        'price_precision': 'price_precision',
        'is_emailed': 'is_emailed',
        'invoices': 'invoices',
        'purchaseorders': 'purchaseorders',
        'is_test_order': 'is_test_order',
        'refundable_amount': 'refundable_amount',
        'notes': 'notes',
        'terms': 'terms',
        'payment_terms': 'payment_terms',
        'payment_terms_label': 'payment_terms_label',
        'custom_fields': 'custom_fields',
        'page_width': 'page_width',
        'page_height': 'page_height',
        'orientation': 'orientation',
        'created_by_id': 'created_by_id',
        'created_date': 'created_date',
        'last_modified_by_id': 'last_modified_by_id',
        'attachment_name': 'attachment_name',
        'can_send_in_mail': 'can_send_in_mail',
        'salesperson_id': 'salesperson_id',
        'salesperson_name': 'salesperson_name',
        'merchant_id': 'merchant_id',
        'merchant_name': 'merchant_name',
        'balance': 'balance',
        'approvers_list': 'approvers_list',
        'cf_billing_published': 'cf_billing_published',
    },
    "item": {
        'item_id': 'item_id',
        'name': 'name',
        'sku': 'sku',
        'brand': 'brand',
        'quantity': 'quantity',
        'discount_amount': 'discount_amount',
        'discount': 'discount',
        'item_total': 'item_total',
        'manufacturer': 'manufacturer',
        'image_name': 'image_name',
        'image_type': 'image_type',
        'status': 'status',
        'source': 'source',
        'is_linked_with_zohocrm': 'is_linked_with_zohocrm',
        'zcrm_product_id': 'zcrm_product_id',
        'crm_owner_id': 'crm_owner_id',
        'unit': 'unit',
        'description': 'description',
        'rate': 'rate',
        'account_id': 'account_id',
        'account_name': 'account_name',
        'tax_id': 'tax_id',
        'associated_template_id': 'associated_template_id',
        'documents': 'documents',
        'tax_name': 'tax_name',
        'tax_percentage': 'tax_percentage',
        'tax_type': 'tax_type',
        'purchase_description': 'purchase_description',
        'pricebook_rate': 'pricebook_rate',
        'sales_rate': 'sales_rate',
        'purchase_rate': 'purchase_rate',
        'purchase_account_id': 'purchase_account_id',
        'purchase_account_name': 'purchase_account_name',
        'created_time': 'created_time',
        'last_modified_time': 'last_modified_time',
        'tags': 'tags',
        'item_type': 'item_type',
        'is_taxable': 'is_taxable',
        'tax_exemption_id': 'tax_exemption_id',
        'tax_exemption_code': 'tax_exemption_code',
        'item_custom_fields': 'item_custom_fields',
        'sales_channels': 'sales_channels'
    },
    "custom_fields": {
        'label': 'label',
        'value': 'value',
    },
    'invoice': {
        'invoice_id': 'invoice_id',
        'invoice_number': 'invoice_number',
        'salesorder_id': 'salesorder_id',
        'salesorder_number': 'salesorder_number',
        'inprocess_transaction_present': 'inprocess_transaction_present',
        'ach_payment_initiated': 'ach_payment_initiated',
        'reader_offline_payment_initiated': 'reader_offline_payment_initiated',
        'is_backorder': 'is_backorder',
        'sales_channel': 'sales_channel',
        'status': 'status',
        'color_code': 'color_code',
        'current_sub_status_id': 'current_sub_status_id',
        'current_sub_status': 'current_sub_status',
        'payment_terms': 'payment_terms',
        'payment_terms_label': 'payment_terms_label',
        'due_date': 'due_date',
        'payment_expected_date': 'payment_expected_date',
        'payment_discount': 'payment_discount',
        'stop_reminder_until_payment_expected_date': 'stop_reminder_until_payment_expected_date',
        'last_payment_date': 'last_payment_date',
        'reference_number': 'reference_number',
        'customer_id': 'customer_id',
        'estimate_id': 'estimate_id',
        'is_client_review_settings_enabled': 'is_client_review_settings_enabled',
        'contact_category': 'contact_category',
        'customer_name': 'customer_name',
        'unused_retainer_payments': 'unused_retainer_payments',
        'contact_persons': 'contact_persons',
        'currency_id': 'currency_id',
        'currency_code': 'currency_code',
        'currency_symbol': 'currency_symbol',
        'exchange_rate': 'exchange_rate',
        'discount_amount': 'discount_amount',
        'discount': 'discount',
        'discount_applied_on_amount': 'discount_applied_on_amount',
        'is_discount_before_tax': 'is_discount_before_tax',
        'discount_type': 'discount_type',
        'recurring_invoice_id': 'recurring_invoice_id',
        'documents': 'documents',
        'is_viewed_by_client': 'is_viewed_by_client',
        'client_viewed_time': 'client_viewed_time',
        'is_inclusive_tax': 'is_inclusive_tax',
        'schedule_time': 'schedule_time',
        'line_items': 'line_items',
        'submitter_id': 'submitter_id',
        'approver_id': 'approver_id',
        'submitted_date': 'submitted_date',
        'submitted_by': 'submitted_by',
        'ach_supported': 'ach_supported',
        'salesorders': 'salesorders',
        'deliverychallans': 'deliverychallans',
        'shipping_charge': 'shipping_charge',
        'adjustment': 'adjustment',
        'roundoff_value': 'roundoff_value',
        'adjustment_description': 'adjustment_description',
        'transaction_rounding_type': 'transaction_rounding_type',
        'sub_total': 'sub_total',
        'tax_total': 'tax_total',
        'discount_total': 'discount_total',
        'total': 'total',
        'discount_percent': 'discount_percent',
        'bcy_shipping_charge': 'bcy_shipping_charge',
        'bcy_adjustment': 'bcy_adjustment',
        'bcy_sub_total': 'bcy_sub_total',
        'bcy_discount_total': 'bcy_discount_total',
        'bcy_tax_total': 'bcy_tax_total',
        'bcy_total': 'bcy_total',
        'taxes': 'taxes',
        'payment_reminder_enabled': 'payment_reminder_enabled',
        'can_send_invoice_sms': 'can_send_invoice_sms',
        'payment_made': 'payment_made',
        'credits_applied': 'credits_applied',
        'tax_amount_withheld': 'tax_amount_withheld',
        'balance': 'balance',
        'write_off_amount': 'write_off_amount',
        'allow_partial_payments': 'allow_partial_payments',
        'price_precision': 'price_precision',
        'payment_options': 'payment_options',
        'is_emailed': 'is_emailed',
        'reminders_sent': 'reminders_sent',
        'last_reminder_sent_date': 'last_reminder_sent_date',
        'next_reminder_date_formatted': 'next_reminder_date_formatted',
        'notes': 'notes',
        'terms': 'terms',
        'custom_fields': 'custom_fields',
        'custom_field_hash': 'custom_field_hash',
        'page_width': 'page_width',
        'page_height': 'page_height',
        'orientation': 'orientation',
        'created_time': 'created_time',
        'last_modified_time': 'last_modified_time',
        'created_date': 'created_date',
        'created_by_id': 'created_by_id',
        'last_modified_by_id': 'last_modified_by_id',
        'attachment_name': 'attachment_name',
        'can_send_in_mail': 'can_send_in_mail',
        'salesperson_id': 'salesperson_id',
        'salesperson_name': 'salesperson_name',
        'merchant_id': 'merchant_id',
        'merchant_name': 'merchant_name',
        'ecomm_operator_id': 'ecomm_operator_id',
        'ecomm_operator_name': 'ecomm_operator_name',
        'is_autobill_enabled': 'is_autobill_enabled',
        'invoice_url': 'invoice_url',
        'sub_total_inclusive_of_tax': 'sub_total_inclusive_of_tax',
        'subject_content': 'subject_content',
        'approvers_list': 'approvers_list',
        'cf_billing_published': 'cf_billing_published',
        },
    'purchase_order':
    {
        'purchaseorder_id': 'purchaseorder_id',
        'documents': 'documents',
        'contact_category': 'contact_category',
        'purchaseorder_number': 'purchaseorder_number',
        'date': 'date',
        'client_viewed_time': 'client_viewed_time',
        'is_viewed_by_client': 'is_viewed_by_client',
        'expected_delivery_date': 'expected_delivery_date',
        'reference_number': 'reference_number',
        'status': 'status',
        'order_status': 'order_status',
        'billed_status': 'billed_status',
        'color_code': 'color_code',
        'current_sub_status_id': 'current_sub_status_id',
        'current_sub_status': 'current_sub_status',
        # 'vendor_id': 'customer_id',
        'vendor_name': 'customer_name',
        'currency_id': 'currency_id',
        'currency_code': 'currency_code',
        'currency_symbol': 'currency_symbol',
        'exchange_rate': 'exchange_rate',
        'delivery_date': 'delivery_date',
        'is_emailed': 'is_emailed',
        'is_inclusive_tax': 'is_inclusive_tax',
        'line_items': 'line_items',
        'has_qty_cancelled': 'has_qty_cancelled',
        'adjustment': 'adjustment',
        'adjustment_description': 'adjustment_description',
        'discount_amount': 'discount_amount',
        'discount': 'discount',
        'discount_applied_on_amount': 'discount_applied_on_amount',
        'is_discount_before_tax': 'is_discount_before_tax',
        'discount_account_id': 'discount_account_id',
        'sub_total': 'sub_total',
        'sub_total_inclusive_of_tax': 'sub_total_inclusive_of_tax',
        'tax_total': 'tax_total',
        'total': 'total',
        'taxes': 'taxes',
        'price_precision': 'price_precision',
        'submitted_date': 'submitted_date',
        'submitted_by': 'submitted_by',
        'submitter_id': 'submitter_id',
        'approver_id': 'approver_id',
        'approvers_list': 'approvers_list',
        'notes': 'notes',
        'terms': 'terms',
        'payment_terms': 'payment_terms',
        'payment_terms_label': 'payment_terms_label',
        'ship_via': 'ship_via',
        'ship_via_id': 'ship_via_id',
        'attention': 'attention',
        'delivery_org_address_id': 'delivery_org_address_id',
        'delivery_customer_id': 'delivery_customer_id',
        'delivery_customer_address_id': 'delivery_customer_address_id',
        'delivery_address': 'delivery_address',
        'custom_fields': 'custom_fields',
        'attachment_name': 'attachment_name',
        'can_send_in_mail': 'can_send_in_mail',
        'page_width': 'page_width',
        'page_height': 'page_height',
        'orientation': 'orientation',
        'template_type': 'template_type',
        'created_time': 'created_time',
        'created_by_id': 'created_by_id',
        'last_modified_time': 'last_modified_time',
        'can_mark_as_bill': 'can_mark_as_bill',
        'can_mark_as_unbill': 'can_mark_as_unbill',
        'salesorders': 'salesorders',
        'bills': 'bills',
        'cf_billing_published': 'cf_billing_published',
        'cf_legal_business_name': 'cf_legal_business_name'
    },
    'package': {
        'salesorder_id': 'salesorder_id',
        'salesorder_number': 'salesorder_number',
        'salesorder_date': 'salesorder_date',
        'package_id': 'package_id',
        'package_number': 'package_number',
        'shipment_id': 'shipment_id',
        'shipment_number': 'shipment_number',
        'date': 'date',
        'shipping_date': 'shipping_date',
        'delivery_method': 'delivery_method',
        'delivery_method_id': 'delivery_method_id',
        'tracking_number': 'tracking_number',
        'tracking_link': 'tracking_link',
        'expected_delivery_date': 'expected_delivery_date',
        'shipment_delivered_date': 'shipment_delivered_date',
        'status': 'status',
        'detailed_status': 'detailed_status',
        'status_message': 'status_message',
        'carrier': 'carrier',
        'service': 'service',
        'delivery_days': 'delivery_days',
        'delivery_guarantee': 'delivery_guarantee',
        'total_quantity': 'total_quantity',
        'customer_id': 'customer_id',
        'customer_name': 'customer_name',
        'email': 'email',
        'phone': 'phone',
        'mobile': 'mobile',
        'contact_persons': 'contact_persons',
        'created_by_id': 'created_by_id',
        'last_modified_by_id': 'last_modified_by_id',
        'notes': 'notes',
        'line_items': 'line_items',
        'is_emailed': 'is_emailed',
        'shipmentorder_custom_fields': 'shipmentorder_custom_fields',
        'picklists': 'picklists',
        'created_time': 'created_time',
        'last_modified_time': 'last_modified_time',
        'shipment_order': 'shipment_order'
        },
    'salesorder_line_item': {
        'so_line_item_id': 'line_item_id',
        'quantity': 'quantity'
    }
}