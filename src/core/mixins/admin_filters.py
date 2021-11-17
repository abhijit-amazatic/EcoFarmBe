from django.contrib.admin import SimpleListFilter, FieldListFilter
from django.utils.translation import ugettext_lazy as _

class NullListFilter(FieldListFilter):

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg_isnull = '%s__isnull' % field_path
        lookup_choices = self.lookups(request, model_admin)
        if lookup_choices is None:
            lookup_choices = ()
        self.lookup_choices = list(lookup_choices)
        super().__init__(field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg_isnull]

    def lookups(self, request, model_admin):
        return (
            ('1', 'Null', ),
            ('0', 'Not Null', ),
        )

    def choices(self, changelist):
        yield {
            'selected': self.used_parameters.get(self.lookup_kwarg_isnull) is None,
            'query_string': changelist.get_query_string(remove=[self.lookup_kwarg_isnull]),
            'display': _('All'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.used_parameters.get(self.lookup_kwarg_isnull) is (lookup == '1'),
                'query_string': changelist.get_query_string({self.lookup_kwarg_isnull: lookup}),
                'display': title,
            }
