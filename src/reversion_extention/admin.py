# from django.contrib import admin
# from reversion.admin import VersionAdmin as VersionAdminBase
# # Register your models here.


# class VersionAdmin(VersionAdminBase):

#     history_latest_first = True
#     change_list_template = "reversion/change_list.html"
#     object_history_template = "reversion_extention/object_history.html"

#     def log_addition(self, request, object, message):
#         change_message = message or _("Initial version.")
#         return super(VersionAdminBase, self).log_change(request, object, change_message)

#     def log_change(self, request, object, message):
#         return super(VersionAdminBase, self).log_change(request, object, message)


from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.contrib.admin import options
from django.contrib.admin.utils import unquote, quote
from django.contrib.contenttypes.admin import GenericInlineModelAdmin
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, re_path
from django.utils.text import capfirst
from django.utils.timezone import template_localtime
from django.utils.translation import ugettext as _
from django.utils.encoding import force_str
from django.utils.formats import localize
from django.db import (
    router,
)
from django.utils.html import mark_safe
from django.template.defaultfilters import truncatewords_html, linebreaksbr
from reversion.models import Version
from reversion.revisions import is_active, register, is_registered, set_comment, create_revision, set_user, _get_content_type

from reversion.models import Revision, Version
from .models import ReversionMeta

from django.contrib.admin import AdminSite
from import_export.admin import (ImportExportModelAdmin, ExportActionMixin)
from import_export import resources




class RevisionResource(resources.ModelResource):

    class Meta:
        model = Revision
        fields = (
            'id',
            'date_created', 
            'user__email',
            'reversion_meta__ip_address',
            'reversion_meta__user_agent',
            'reversion_meta__path',
            'comment',
        )
        export_order = ( 'id',
                         'date_created', 
                         'user__email',
                         'reversion_meta__ip_address',
                         'reversion_meta__user_agent',
                         'reversion_meta__path',
                         'comment')
        
        
class RevisionAdmin(ExportActionMixin,admin.ModelAdmin):
    model = Revision
    change_form_template = "reversion_extention/change_form.html"
    list_display=('date_created', 'user', 'ip_address', 'user_agent', 'path', 'changes_trunc')
    resource_class = RevisionResource
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'date_created',
            ),
        }),
        ('Meta', {
            'fields': (
                'ip_address',
                'user_agent',
                'path',
            ),
        }),
        ('Change info', {
            'fields': (
                'changes',
            ),
        }),
    )


    class Meta:
        model = Revision
        fields = '__all__'

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs.select_related('reversion_meta')
        qs.select_related('version_set')
        return qs

    def ip_address(self, obj):
        try:
            return obj.reversion_meta.ip_address
        except:
            return ''

    def user_agent(self, obj):
        try:
            return obj.reversion_meta.user_agent
        except:
            return ''

    def path(self, obj):
        try:
            return obj.reversion_meta.path
        except:
            return ''


    def changes(self, obj):
        return linebreaksbr(mark_safe(obj.comment)) or ''
    changes.short_description = 'Changes'
    changes.allow_tags = True

    def changes_trunc(self, obj):
        return truncatewords_html(linebreaksbr(mark_safe(obj.comment)), 10)
    changes.short_description = 'Changes'
    changes.allow_tags = True





# reversion_admin = type("%sAdmin" % Revision.__name__, (RevisionAdmin,), {})(Revision, admin.site)

# reversion_admin.register(Version, admin.ModelAdmin)
admin.site.register(Revision, RevisionAdmin)
# reversion_admin.register(ReversionMeta, admin.ModelAdmin)
# admin.site.register(ReversionMeta, admin.ModelAdmin)



class VersionAdmin(admin.ModelAdmin):

    object_history_template = "reversion_extention/object_history.html"

    # change_list_template = "reversion_extention/change_list.html"

    revision_form_template = "reversion_extention/revision_form.html"

    history_latest_first = True

    def reversion_register(self, model, **kwargs):
        """Registers the model with reversion."""
        register(model, **kwargs)

    # Revision helpers.

    def _reversion_order_version_queryset(self, queryset):
        """Applies the correct ordering to the given version queryset."""
        if not self.history_latest_first:
            queryset = queryset.order_by("pk")
        return queryset

    # Messages.

    # def log_addition(self, request, object, message):
    #     change_message = message or _("Initial version.")
    #     entry = super().log_addition(request, object, change_message)
    #     if is_active():
    #         set_comment(entry.get_change_message())
    #     return entry

    # def log_change(self, request, object, message):
    #     entry = super().log_change(request, object, message)
    #     if is_active():
    #         set_comment(entry.get_change_message())
    #     return entry

    # Auto-registration.

    def _reversion_autoregister(self, model, follow):
        if not is_registered(model):
            for parent_model, field in model._meta.concrete_model._meta.parents.items():
                follow += (field.name,)
                self._reversion_autoregister(parent_model, ())
            self.reversion_register(model, follow=follow)

    def _reversion_introspect_inline_admin(self, inline):
        inline_model = None
        follow_field = None
        fk_name = None
        if issubclass(inline, GenericInlineModelAdmin):
            inline_model = inline.model
            ct_field = inline.ct_field
            fk_name = inline.ct_fk_field
            for field in self.model._meta.private_fields:
                if (
                    isinstance(field, GenericRelation) and
                    field.remote_field.model == inline_model and
                    field.object_id_field_name == fk_name and
                    field.content_type_field_name == ct_field
                ):
                    follow_field = field.name
                    break
        elif issubclass(inline, options.InlineModelAdmin):
            inline_model = inline.model
            fk_name = inline.fk_name
            if not fk_name:
                for field in inline_model._meta.get_fields():
                    if (
                        isinstance(field, (models.ForeignKey, models.OneToOneField)) and
                        issubclass(self.model, field.remote_field.model)
                    ):
                        fk_name = field.name
                        break
            if fk_name and not inline_model._meta.get_field(fk_name).remote_field.is_hidden():
                field = inline_model._meta.get_field(fk_name)
                accessor = field.remote_field.get_accessor_name()
                follow_field = accessor
        return inline_model, follow_field

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Automatically register models if required.
        self.inline_info = ()
        if not is_registered(self.model):
            inline_fields = ()
            for inline in self.inlines:
                inline_model, follow_field = self._reversion_introspect_inline_admin(inline)
                self.inline_info += ((inline_model, follow_field),)
                if inline_model:
                    self._reversion_autoregister(inline_model, ())
                if follow_field:
                    inline_fields += (follow_field,)
            self._reversion_autoregister(self.model, inline_fields)

    def get_urls(self):
        urls = super().get_urls()
        admin_site = self.admin_site
        opts = self.model._meta
        info = opts.app_label, opts.model_name,
        reversion_urls = [
            re_path(
                r"^([^/]+)/history/(\d+)/$",
                admin_site.admin_view(self.revision_view),
                name='%s_%s_revision' % info,
            ),
        ]
        return reversion_urls + urls

    def revision_view(self, request, object_id, version_id, extra_context=None):
        """Displays the contents of the given revision."""
        object_id = unquote(object_id)  # Underscores in primary key get quoted to "_5F"
        # version = get_object_or_404(Version, pk=version_id, object_id=object_id)        
        obj_main = get_object_or_404(self.model, pk=object_id)
        # version = get_object_or_404(Version, pk=version_id,)
        revision = get_object_or_404(Revision, pk=version_id,)

        context = {
            "title": _("Revert %(name)s") % {"name": str(revision.pk)},
            "revert": True,
            "parent_object_id": object_id,
            "parent_opts": self.model._meta,
            "Parent_name":str(obj_main) or str(revision)

        }
        context.update(extra_context or {})
        # admin_obj = RevisionAdmin(model=version.revision.__class__, admin_site=self.admin_site.name)
        admin_obj = admin.site._registry[Revision]
        # admin_obj = reversion_admin
        response = admin_obj.changeform_view(request, quote(str(revision.pk)), request.path, context)
        # response = self.changeform_view(request, quote(version.object_id), request.path, context)
        response.template_name = self.revision_form_template
        response.render()  #
        return response


    def history_view(self, request, object_id, extra_context=None):
        """Renders the history view."""
        # Check if user has view or change permissions for model
        if hasattr(self, 'has_view_or_change_permission'):  # for Django >= 2.1
            if not self.has_view_or_change_permission(request):
                raise PermissionDenied
        else:
            if not self.has_change_permission(request):
                raise PermissionDenied

        opts = self.model._meta
        q = self.get_version_query_q(self.model, object_id)
        try:
            obj_main = self.model.objects.get(pk=quote(object_id))
        except self.model.DoesNotExist:
            pass
        else:
            for model, field in self.inline_info:
                if hasattr(obj_main, field):
                    obj = getattr(obj_main, field, '')
                    if obj:
                        if isinstance(obj, models.Model):
                            q |= self.get_version_query_q(model, obj.pk)
        pre_fix = reverse("%s:%s_%s_history" % (self.admin_site.name, opts.app_label, opts.model_name),
                    args=(object_id,))
        # action_list = [
        #     {
        #         "revision": version.revision,
        #         "url": pre_fix + str(version.revision.id) + '/',
        #     }
        #     for version
        #     in self._reversion_order_version_queryset(Version.objects.filter(q).select_related("revision__user").select_related("revision__reversion_meta"))
        # ]
        revision_ids = Version.objects.filter(q).values_list('revision_id', flat=True).distinct()
        action_list = [
            {
                "revision": revision,
                "url": reverse(
                    "%s:%s_%s_revision" % (self.admin_site.name, opts.app_label, opts.model_name),
                    args=(quote(object_id), revision.id)
                ),
            }
            for revision
            in self._reversion_order_version_queryset(Revision.objects.filter(id__in=revision_ids).select_related("user").select_related("reversion_meta"))
        ]
        # Compile the context.
        context = {"action_list": action_list}
        context.update(extra_context or {})
        return super().history_view(request, object_id, context)


    def get_version_query_q(self, model, obj_id):
        model_db = router.db_for_write(model)
        content_type = _get_content_type(model, model_db)
        return Q(
            content_type=content_type,
            object_id=obj_id,
            db=model_db,
        )

