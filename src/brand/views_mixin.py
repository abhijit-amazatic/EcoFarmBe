from django.db.models import Q
from django.http import Http404
from rest_framework.exceptions import (NotFound, PermissionDenied,)


from .permissions import filterQuerySet
from . import models

class NestedViewSetMixin:
    context_parent = dict()
    parent_field_default = dict()
    url_params_model_map = {
        'organization': models.Organization,
        'organization_user': models.OrganizationUser,
        'brand': models.Brand,
        'license': models.License,
    }

    def get_queryset(self):
        return self.filter_queryset_by_parents_lookups(
            super().get_queryset()
    )

    # def filter_queryset_by_parents_lookups(self, queryset):
    #     parents_query_dict = self.get_parents_query_dict()
    #     if parents_query_dict:
    #         try:
    #             return queryset.filter(**parents_query_dict)
    #         except ValueError:
    #             raise Http404
    #     else:
    #         return queryset

    def filter_queryset_by_parents_lookups(self, queryset):
        if self.parent_field_default:
            try:
                return queryset.filter(**self.parent_field_default)
            except ValueError:
                raise Http404
        else:
            return queryset

    def get_parents_query_dict(self, **kwargs):
        result = {}
        for kwarg_name, kwarg_value in self.kwargs.items():
            if kwarg_name.startswith('parent_'):
                query_lookup = kwarg_name.replace(
                    'parent_',
                    '',
                    1
                )
                query_value = kwarg_value
                result[query_lookup] = query_value
        return result

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        lookup_param = self.get_parents_query_dict()
        nested_parent = {}
        for key, value in lookup_param.items():
            model = self.url_params_model_map.get(key)
            if model:
                qs = filterQuerySet.for_user(
                    model.objects.all(),
                    self.request.user,
                )
                filter_param = {'pk': value}
                filter_param.update(nested_parent)
                qs = qs.filter(**filter_param)
                if not qs.exists():
                    raise PermissionDenied(detail=f'{key} does not exist or not accessible.')
                else:
                    obj = qs.first()
                    self.context_parent[key] = obj
                    self.parent_field_default = {key: obj}
                    nested_parent_updated = {}
                    for p_key, p_value in nested_parent.items():
                        nested_parent_updated[key+'__'+p_key] = p_value


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(self.context_parent)
        context['parent_field_default'] = self.parent_field_default
        return context

class PermissionQuerysetFilterMixin:

    def filter_queryset(self, queryset):
        queryset = filterQuerySet.filter_queryset(self.request, queryset, self)
        return super().filter_queryset(queryset)
