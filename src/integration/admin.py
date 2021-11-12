import requests
import copy
from datetime import (datetime, timedelta)
from urllib.parse import urlencode
from django.utils import timezone
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http.response import (
    HttpResponseBase,
    HttpResponseRedirect,
    HttpResponse,
    HttpResponseForbidden,
)
from django.urls import path, reverse

from core import settings
from core.mixins.admin import (CustomButtonMixin,)
from utils import reverse_admin_change_path
from .models import (Integration,ConfiaCallback)
from .admin_config import INTEGRATION_OAUTH_MAP

class IntegrationAdmin(CustomButtonMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = (
        'name',
        'client_id',
        'client_secret',
        'access_token_masked',
        'access_expiry',
        'expiry_time',
        'refresh_token_masked',
        'refresh_expiry',
    )
    readonly_fields = (
        'name',
        'client_id',
        'client_secret',
        'access_token_masked',
        'access_expiry',
        'expiry_time',
        'refresh_token_masked',
        'refresh_expiry',
    )
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'client_id',
                'client_secret',
                'access_token_masked',
                'access_expiry',
                'expiry_time',
                'refresh_token_masked',
                'refresh_expiry',
            ),
        }),
    )
    ordering = ('name',)

    custom_buttons = ('generate_new_tokens',)
    custom_buttons_prop = {
        'generate_new_tokens': {
            'label': 'Generate New Tokens',
            'color': '#ba2121',
        }
    }
    req_headers = {'content-type': 'application/x-www-form-urlencoded'}

    def show_generate_new_tokens_button(self, request, obj,  add=False, change=False):
        if obj and obj.name in INTEGRATION_OAUTH_MAP:
            return True
        return False

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return request.user.email in getattr(settings, 'INTEGRATION_ADMIN_EMAILS', [])
        return False

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_params(self, oauth_info, action):
        query_params = dict(**oauth_info.get('params', {}).get(action, {}))
        for k in query_params:
            if not query_params[k] and  k in oauth_info:
                query_params[k] = oauth_info[k]
        return query_params


    def generate_new_tokens(self, request, obj):
        if obj and obj.name in INTEGRATION_OAUTH_MAP:
            oauth_info = INTEGRATION_OAUTH_MAP[obj.name]
            query_params = self.get_params(oauth_info, 'redirect_uri')
            try:
                query_params['state'] = obj.name
                auth_url = oauth_info['auth_url'].rstrip('?') + "?" + urlencode(query_params)
            except KeyError:
                pass
            else:
                return HttpResponseRedirect(auth_url)

    def get_urls(self):
        urls = super().get_urls()
        admin_site = self.admin_site
        opts = self.model._meta
        integration_urls = [
            path(
                "oauth_callback",
                admin_site.admin_view(self.oauth_callback),
                name='%s_oauth_callback' % opts.app_label,
            ),
        ]
        return integration_urls + urls

    def oauth_callback(self, request, *args, **kwargs):
        if not self.has_view_or_change_permission(request):
            return HttpResponseForbidden('<h1>403 Forbidden</h1>')
        state = request.GET.get('state', None)
        if state:
            if state in INTEGRATION_OAUTH_MAP:
                update_data = dict()
                oauth_info = INTEGRATION_OAUTH_MAP[state]
                auth_code_callback_kw_name = oauth_info.get('auth_code_callback_kw_name', 'code')
                auth_code = request.GET.get(auth_code_callback_kw_name)
                if auth_code:
                    query_params = self.get_params(oauth_info, 'authenticate')
                    query_params['code'] = auth_code
                    # if 'redirect_uri' in query_params:
                    #     query_params['redirect_uri'] = self.get_redirect_uri(request)

                    time_now = timezone.now()

                    response = requests.post(url=oauth_info['access_token_url'], data=query_params, headers=self.req_headers)
                    if response.status_code == 200:
                        resp_data = response.json()
                        if resp_data.get('refresh_token'):
                            update_data['refresh_token'] = resp_data.get('refresh_token')
                            if resp_data.get('access_token'):
                                update_data['access_token'] = resp_data.get('access_token')
                                if resp_data.get('expires_in'):
                                    expire_in_delta = timedelta(seconds=resp_data.get('expires_in'))
                                    update_data['access_expiry'] = time_now + expire_in_delta
                                if oauth_info.get('client_id'):
                                    update_data['client_id'] = oauth_info.get('client_id')
                                if oauth_info.get('client_secret'):
                                    update_data['client_secret'] = oauth_info.get('client_secret')
                    else:
                        self.message_user(request, response.text, level='error')
                else:
                    self.message_user(request, dict(request.GET), level='error')

                try:
                    obj = self.model.objects.get(name=state)
                except self.model.DoesNotExist:
                    if not update_data:
                        return HttpResponse('Unable to get authorization code')
                    else:
                        if update_data:
                            obj = self.model.objects.create(name=state, **update_data)
                            self.message_user(request, "Tokens added successfully.", level='success')
                            return HttpResponseRedirect(reverse_admin_change_path(obj))
                else:
                    if update_data:
                        old_refresh_token = obj.refresh_token
                        old_access_token = obj.access_token
                        obj.__dict__.update(update_data)
                        obj.save()
                        self.message_user(request, "Tokens updated successfully.", level='success')
                        if not settings.DEBUG:
                            self.revoke_token(oauth_info, old_refresh_token, token_type=state+' refresh')
                            self.revoke_token(oauth_info, old_access_token, token_type=state+' access')
                    return HttpResponseRedirect(reverse_admin_change_path(obj))
            else:
                return HttpResponse('Integration for current state Not Supported')
        else:
            return HttpResponse('state not provided.')

    def revoke_token(self, oauth_info, token, token_type):
        query_params = self.get_params(oauth_info, 'revoke_token')
        query_params['token'] = token
        response = requests.post(url=oauth_info['revoke_token_url'], data=query_params, headers=self.req_headers)
        if not response.ok:
            print(f"Old {token_type} token revoke response:", response.text)
        return response

    def get_redirect_uri(self, request):
        return request.build_absolute_uri(
            reverse(
                'admin:%s_oauth_callback' % self.model._meta.app_label,
                current_app=self.admin_site.name,
            )
        )

    def access_token_masked(self, obj):
        if obj.access_token and settings.INTEGRATION_ADMIN_TOKEN_MASK:
            mask_len = int(len(obj.access_token)*0.9)
            return ('*'*mask_len) + obj.access_token[mask_len:]
        else:
            return obj.access_token
    access_token_masked.short_description = 'Access Token'

    def refresh_token_masked(self, obj):
        if obj.refresh_token and settings.INTEGRATION_ADMIN_TOKEN_MASK:
            mask_len = int(len(obj.refresh_token)*0.9)
            return ('*'*mask_len) + obj.refresh_token[mask_len:]
        else:
            return obj.refresh_token
    refresh_token_masked.short_description = 'Refresh Token'


class ConfiaCallbackAdmin(admin.ModelAdmin):
    """
    ConfiaCallbackAdmin
    """
    list_display = ('partner_company_id', 'confia_member_id','status','created_on','updated_on')
    list_filter = ('partner_company_id',)
    list_per_page = 25
    search_fields = ('partner_company_id','confia_member_id',)
    ordering = ('-created_on',)
    readonly_fields = ('partner_company_id', 'confia_member_id','status','created_on','updated_on',)
    fields = ('partner_company_id', 'confia_member_id', 'status','created_on','updated_on')
    
admin.site.register(Integration, IntegrationAdmin)
admin.site.register(ConfiaCallback, ConfiaCallbackAdmin)
