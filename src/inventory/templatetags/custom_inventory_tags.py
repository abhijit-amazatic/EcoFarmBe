from django import template
from django.utils.translation import ugettext
from django.contrib.admin.templatetags.admin_modify import submit_row
from django.contrib.admin.templatetags.base import InclusionAdminNode

register = template.Library()


@register.tag(name='submit_row_custom_inv')
def submit_row_custom_inv_tag(parser, token):
    return InclusionAdminNode(parser, token, func=submit_row, template_name='custom_inventory_submit_line.html')
