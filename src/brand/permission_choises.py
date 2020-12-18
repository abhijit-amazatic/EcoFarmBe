from django.utils.translation import ugettext_lazy as _

GROUP_ORDERS = 'orders'
GROUP_PROFILE = 'profile'
GROUP_COMPLIANCE = 'comliance'
GROUP_MARKETPLACE = 'marketplce'
GROUP_BILLING_AND_ACCOUNTING = 'billing_and_accounting'

GROUP_CHOICES = (
    (GROUP_ORDERS, _('orders')),
    (GROUP_PROFILE, _('Profile')),
    (GROUP_COMPLIANCE, _('Compliance')),
    (GROUP_MARKETPLACE, _('Marketplace')),
    (GROUP_BILLING_AND_ACCOUNTING, _('Billing & Accounting')),
)

PERMISSION_CHOICES_ORG = (
    (GROUP_ORDERS, (
        ('create_order', _('Create Order')),
        ('sign_order', _('Sign Order')),
    )),
    (GROUP_PROFILE, (
        ('view_profile', _('View Profile')),
    )),
    (GROUP_COMPLIANCE, (
        ('view_license', _('View License')),
        ('edit_license', _('Edit License')),
        ('add_license', _('Add License')),
        ('delete_license', _('Delete License')),
    )),
    (GROUP_MARKETPLACE, (
        ('view_pricing', _('View Pricing')),
        ('view_labtest', _('View Lab Test')),
    )),
    (GROUP_BILLING_AND_ACCOUNTING, (
        ('view_bills', _('View Bills')),
    )),
)
GROUP_CHOICES_DICT = dict(GROUP_CHOICES)
PERMISSION_CHOICES = list()
for x in PERMISSION_CHOICES_ORG:
    PERMISSION_CHOICES.append((GROUP_CHOICES_DICT[x[0]], x[1]))
PERMISSION_CHOICES = tuple(PERMISSION_CHOICES)
PERMISSION_CHOICES_DICT = dict((x for y, z in PERMISSION_CHOICES for x in z))
PERMISSION_GROUP_MAP = dict((a, x) for x, y in PERMISSION_CHOICES_ORG for a, b in y)
