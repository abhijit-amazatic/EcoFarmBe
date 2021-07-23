from os import urandom
from django import forms
from django.contrib.admin import widgets
from django.contrib import admin
from django.db import models
from django.db.models.query import QuerySet
from django.http.response import HttpResponseBase, HttpResponseRedirect
from django.utils import timezone



class CustomButtonMixin:
    """
    Admin change form with custom buttons and method call.
    """
    custom_buttons = ()
    change_form_template = 'admin/custom_button_change_form.html'

    def show_button(self, button_name, request, obj, add=False, change=False):
        if hasattr(self, f'show_{button_name}_button'):
            return getattr(self, f'show_{button_name}_button', self.show_button)(request, obj, add=add, change=change)
        return change

    def response_change(self, request, obj):
        for button in self.custom_buttons:
            if f'_{button}' in request.POST:
                if self.show_button(button, request, obj, change=True):
                    resp = getattr(self, button, lambda x, y: None)(request, obj)
                    if resp and issubclass(type(resp), HttpResponseBase):
                        return resp
                return HttpResponseRedirect('.')
        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        for button in self.custom_buttons:
            if f'_{button}' in request.POST:
                if self.show_button(button, request, obj, add=True):
                    resp = getattr(self, button, lambda x, y: None)(request, obj)
                    if resp and issubclass(type(resp), HttpResponseBase):
                        return resp
                return HttpResponseRedirect('.')
        return super().response_add(request, obj, post_url_continue=post_url_continue)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['custom_buttons'] = list(self.custom_buttons)
        for button in self.custom_buttons:
            context[f'show_{button}'] = self.show_button(button, request, obj, add, change)
            context[f'{button}_button_label'] = getattr(self, 'custom_buttons_prop', {}).get(button, {}).get('label', button.title())
            context[f'{button}_button_color'] = getattr(self, 'custom_buttons_prop', {}).get(button, {}).get('color', '#21ba21')
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)


