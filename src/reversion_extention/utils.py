import json
from django.db.models import AutoField, DateTimeField
from django.db.models.fields.related import RelatedField, ManyToManyField
from django.contrib.postgres.fields import (ArrayField, JSONField,)

from reversion_compare.helpers import html_diff

import reversion
obj_title_msg = "{verbose_name} \"<strong>{obj_name}</strong>\""
changes_title_template = '{0} was changed:'
was_created_message = "{0} was created.\n\n"
was_deleted_message = "{0} was deleted.\n\n"
saved_without_changes_message = "{0} saved without changes.\n\n"

changes_template = ("<li>{verbose_name}: \"<strong>{value_from}</strong>\" "
                    "to \"<strong>{value_to}</strong>\"</li>")
changes_json_template = "<li>{verbose_name} (Json field): {diff_html}</li>"
no_value_message = 'No value.'


def generate_change_comment(old_instance_deserialized, new_instance_deserialized):
        old_inst_d = old_instance_deserialized
        new_inst_d = new_instance_deserialized
        new_instance = new_inst_d.object
        obj_title = obj_title_msg.format(
            verbose_name=old_instance_deserialized.object._meta.verbose_name.title(),
            obj_name=str(old_instance_deserialized.object),
        )
        comment = []
        for field in sorted(new_instance._meta.fields + new_instance._meta.many_to_many, key = lambda x:x.creation_counter):
            old_value, new_value = field.value_from_object(old_inst_d.object), field.value_from_object(new_instance)
            if isinstance(field, JSONField):
                if old_value != new_value:
                    comment.append(
                        changes_json_template.format(
                            verbose_name=field.verbose_name,
                            diff_html=html_diff(
                                json.dumps(old_value, indent=2),
                                json.dumps(new_value, indent=2),
                            ),
                        )
                    )
            elif not isinstance(field, (AutoField, ManyToManyField)):
                if not isinstance(field, DateTimeField) or not getattr(field, 'auto_now', False):
                    if old_value != new_value:
                        if isinstance(field, RelatedField):
                            comment.append(
                                changes_template.format(
                                    verbose_name=field.verbose_name,
                                    value_from=no_value_message if not old_value else field.related_model.objects.get(pk=old_value),
                                    value_to=no_value_message if not new_value else field.related_model.objects.get(pk=new_value),
                                )
                            )
                        else:
                            comment.append(
                                changes_template.format(
                                    verbose_name=field.verbose_name,
                                    value_from=old_value,
                                    value_to=new_value,
                                )
                            )
            elif isinstance(field, ManyToManyField):
                old_value = old_inst_d.m2m_data[field.name]
                old_value = [pk for pk in old_value] if old_value else old_value
                new_value = new_inst_d.m2m_data[field.name]
                new_value = [pk for pk in new_value] if new_value else new_value
                if old_value != new_value:
                    A = set(old_value)
                    B = set(new_value)
                    comment.append(f'<li>{field.verbose_name}:\n')
                    if (B-A):
                        added = (str(obj) for obj in field.related_model.objects.filter(pk__in=tuple(B-A)))
                        comment.append('Added: <ul><li>'+ '</li><li>'.join(added)+'</li></ul>')
                    if (A-B):
                        removed = (str(obj) for obj in field.related_model.objects.filter(pk__in=tuple(A-B)))
                        comment.append('Removed: <ul><li>'+ '</li><li>'.join(removed)+'</li></ul>')
                    comment.append('</li>')
        if comment:
            return changes_title_template.format(obj_title)+ '<ul>' + ''.join(comment) + '</ul>'
        else:
            return saved_without_changes_message.format(obj_title)
