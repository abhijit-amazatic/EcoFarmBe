"""
Form widget and field.

PermissionSelectMultipleField
    Permission field handling EXCLUDE_APPS and EXCLUDE_MODELS
    settings.

PermissionSelectMultipleWidget
    The actual permissions widget.
"""
from django import forms
from django import template
from django.db.models import Q
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Permission



class PermissionSelectMultipleWidget(forms.CheckboxSelectMultiple):
    """
    Child of CheckboxSelectMultiple which renders
    `permissions_widget/widget.html` to display the form field.
    """
    default_permission_types = ['view', 'edit', 'add', 'delete']
    custom_permission_types = []
    groups_permissions = []

    def render(self, name, value, attrs=None, choices=(), renderer=None):
        if value is None:
            value = []

        t = get_template('brand/permission_widget.html')
        c = {
            'name': name,
            'value': value,
            'table': self.get_table(),
            'groups_permissions': self.groups_permissions,
            'default_permission_types': self.default_permission_types,
            'custom_permission_types': self.custom_permission_types
        }
        ctx = template.Context(c)

        try:
            # Django < 1.11
            return mark_safe(t.render(ctx))
        except TypeError:
            # Django >= 1.11
            return mark_safe(t.render(c))

    def get_table(self):
        table = []
        row = None
        last_group = None
        last_model = None

        try:
            permissions = self.choices.queryset
        except AttributeError:
            permissions = self.queryset

        for permission in permissions:
            # get permission type from codename
            codename = permission.codename
            model_part = "_" + permission.codename.split('_', 1)[1]
            permission_type = codename
            if permission_type.endswith(model_part):
                permission_type = permission_type[:-len(model_part)]

            # get app label and model verbose name
            group = permission.group
            model_class = model_part
            model_verbose_name = permission.codename.split('_', 1)[1]

            if permission_type not in self.default_permission_types + self.custom_permission_types:
                self.custom_permission_types.append(permission_type)

            # each row represents one model with its permissions categorized by type
            is_app_or_model_different = last_model != model_class or last_group != group
            if is_app_or_model_different:
                row = dict(model=model_verbose_name, model_class=model_class, group=group, permissions={})

            row['permissions'][permission_type] = permission

            if is_app_or_model_different:
                table.append(row)

            last_group = group
            last_model = model_class

        return table

