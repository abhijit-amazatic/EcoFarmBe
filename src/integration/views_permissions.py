from permission.views_permission_base import ViewPermission





class EstimateViewPermission(ViewPermission):
    method_perm_map = {
        'get': 'view_orders_estimates',
        'post': 'add_orders_estimates',
        'put': 'edit_orders_estimates',
        'patch': 'edit_orders_estimates',
        'delete': 'delete_orders_estimates',
    }

class PurchaseOrderViewPermission(ViewPermission):
    method_perm_map = {
        'get': 'view_purchase_orders',
    }

class VendorPaymentViewPermission(ViewPermission):
    method_perm_map = {
        'get': 'view_payments_made',
    }

class CustomerPaymentViewPermission(ViewPermission):
    method_perm_map = {
        'get': 'view_payments_received',
    }

class InvoiceViewPermission(ViewPermission):
    method_perm_map = {
        'get': 'view_invoices',
    }

class BillViewPermission(ViewPermission):
    method_perm_map = {
        'get': 'view_bills',
    }

class SalesOrderViewPermission(ViewPermission):
    method_perm_map = {
        'get': 'view_sales_orders',
    }

