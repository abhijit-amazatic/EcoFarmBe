from django import template
from django.utils.translation import ugettext
from django.contrib.admin.templatetags.base import InclusionAdminNode

register = template.Library()


@register.simple_tag(takes_context=True)
def show_button(context, button_name):
    return context.get(f'show_{button_name}', False)

@register.simple_tag(takes_context=True)
def button_label(context, button_name):
    return context.get(f'{button_name}_button_label')

@register.simple_tag(takes_context=True)
def button_color(context, button_name):
    return context.get(f'{button_name}_button_color')