import time
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize, deserialize
from django.db import models

import reversion
from reversion.revisions import is_active, register, is_registered, set_comment, create_revision, set_user, _get_options
from reversion.models import ObjectDoesNotExist

from .models import ReversionMeta, OldVersion
from .thread_utils import (
    push_seralized_instances,
    get_seralized_instances,
    get_created_obj_info,
    push_created_obj_info,
    get_deleted_obj_info,
    push_deleted_obj_info,
)
from  .utils import (
    generate_change_comment,
    was_created_message,
    was_deleted_message,
    obj_title_msg,
)


def pre_save_handler(sender, instance, **kwargs):
    if is_active() and is_registered(sender):
        version_options = _get_options(sender)
        if instance.pk:
            push_seralized_instances(
                version_options.format,
                serialize(
                    version_options.format,
                    (sender.objects.get(pk=instance.pk),),
                    fields=version_options.fields,
                    use_natural_foreign_keys=version_options.use_natural_foreign_keys,
                ),
            )
    for field in instance._meta.fields:
        if isinstance(field, (models.TimeField, models.DateField, models.DateTimeField)):
            val = instance.__dict__[field.name]
            if isinstance(val, str):
                instance.__dict__[field.name] = field.to_python(val)


def post_save_handler(sender, instance, created, **kwargs):
    if created:
        push_created_obj_info(
            content_type_id=ContentType.objects.get(app_label=sender._meta.app_label, model=sender._meta.model_name).pk,
            object_id=instance.pk,
            verbose_name=str(sender._meta.verbose_name),
            obj_name=str(instance),
        )

def post_delete_handler(sender, instance, **kwrags):
    push_deleted_obj_info(
        content_type_id=ContentType.objects.get(app_label=sender._meta.app_label, model=sender._meta.model_name).pk,
        object_id=instance.pk,
        verbose_name=str(sender._meta.verbose_name),
        obj_name=str(instance),
    )


def post_revision_commit_handler(sender, revision , versions, **kwargs ):
    # time.sleep(10)
    initial_comment = revision.comment
    final_comment = []
    old_instances_data = tuple(
        (format, data, list(deserialize(format, data))[0])
        for format, data in get_seralized_instances()
    )
    try:
        reversion_meta = revision.reversion_meta
    except revision.__class__.reversion_meta.RelatedObjectDoesNotExist:
        pass
    else:
        reversion_meta.created_objects = [
            {
                'content_type_id': x.content_type_id,
                'object_id': x.object_id,
                'verbose_name': x.verbose_name,
                'obj_name': x.obj_name,
            }
            for x in get_created_obj_info()
        ]
        reversion_meta.deleted_objects = [
            {
                'content_type_id': x.content_type_id,
                'object_id': x.object_id,
                'verbose_name': x.verbose_name,
                'obj_name': x.obj_name,
            }
            for x in get_deleted_obj_info()
        ]
        reversion_meta.save()

    for delete_obj in get_deleted_obj_info():
        obj_title = obj_title_msg.format(
            verbose_name=delete_obj.verbose_name,
            obj_name=delete_obj.obj_name,
        )
        comment = was_deleted_message.format(obj_title)
        final_comment.append(comment)

    for version in versions:
        new_instance_deserialized = list(deserialize(version.format, version.serialized_data))[0]
        comment = ''
        for created_obj in get_created_obj_info():
            if version.content_type_id == created_obj.content_type_id and type(created_obj.object_id)(version.object_id) == created_obj.object_id:
                obj_title = obj_title_msg.format(
                    verbose_name=new_instance_deserialized.object._meta.verbose_name.title(),
                    obj_name=str(new_instance_deserialized.object),
                )
                comment = was_created_message.format(obj_title)
                break
        else:
            for old_deserialized_instance_data in old_instances_data:
                old_deserialized_instance = old_deserialized_instance_data[2]
                if old_deserialized_instance.object.__class__ == new_instance_deserialized.object.__class__:
                    if old_deserialized_instance.object.pk == new_instance_deserialized.object.pk:
                        OldVersion.objects.create(
                            version=version,
                            format=old_deserialized_instance_data[0],
                            serialized_data=old_deserialized_instance_data[1],
                        )
                        comment = generate_change_comment(
                            old_instance_deserialized=old_deserialized_instance,
                            new_instance_deserialized=new_instance_deserialized
                        )
                        break
        final_comment.append(comment)

    revision.comment = ''.join(final_comment) or initial_comment
    revision.save()