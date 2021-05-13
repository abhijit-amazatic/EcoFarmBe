from os import urandom
from django import forms
from django.contrib.admin import widgets
from django.contrib import admin
from django.db import models
from django.db.models.query import QuerySet
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone

from ..tasks.notify_item_change_submitted import notify_inventory_item_change_submitted_task
from brand.models import (License, LicenseProfile,)


class AdminApproveMixin:
    """
    Admin change form with aproval button and method call.
    """
    change_form_template = 'inventory/custom_inventory_change_form.html'

    def show_aproval_button(self, request, obj):
        return obj.status == 'pending_for_approval'

    def response_change(self, request, obj):
        if '_approve' in request.POST:
            if self.show_aproval_button(request, obj):
                self.approve(request, obj)
            return HttpResponseRedirect('.')
        return super().response_change(request, obj)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and self.show_aproval_button(request, obj) and change:
            context['show_approve'] = True
        context['approve_button_label'] = getattr(self, 'approve_button_label', 'Approve')
        context['approve_button_color'] = getattr(self, 'approve_button_color', '#21ba21')
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)




