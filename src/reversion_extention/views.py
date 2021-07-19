from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication
# Create your views here.
from functools import wraps

from reversion.revisions import (
    create_revision as create_revision_base,
    set_user,
    get_user,
    add_meta,
)

from .models import ReversionMeta

class _RollBackRevisionView(Exception):

    def __init__(self, response):
        self.response = response


def _request_creates_revision(request):
    return request.method not in ("OPTIONS", "GET", "HEAD")


def _set_user_from_request(request):
    if get_user() is None:
        if getattr(request, "user", None) and request.user.is_authenticated:
            set_user(request.user)
        else:
            auth_head = request.META.get('HTTP_AUTHORIZATION')
            if auth_head and not request.user.is_authenticated:
                token_auth = TokenAuthentication()
                try:
                    user, _ = token_auth.authenticate(request)
                    set_user(user)
                except Exception:
                    pass


def create_revision(manage_manually=False, using=None, atomic=True, request_creates_revision=None):
    """
    View decorator that wraps the request in a revision.

    The revision will have it's user set from the request automatically.
    """
    request_creates_revision = request_creates_revision or _request_creates_revision

    def decorator(func):
        @wraps(func)
        def do_revision_view(request, *args, **kwargs):
            if request_creates_revision(request):
                try:
                    with create_revision_base(manage_manually=manage_manually, using=using, atomic=atomic):
                        response = func(request, *args, **kwargs)
                        # Check for an error response.
                        if response.status_code >= 400:
                            raise _RollBackRevisionView(response)
                        # Otherwise, we're good.
                        _set_user_from_request(request)
                        add_meta(
                            ReversionMeta,
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT'),
                            path=request.get_full_path_info(),
                        )
                        return response
                except _RollBackRevisionView as ex:
                    return ex.response
            return func(request, *args, **kwargs)
        return do_revision_view
    return decorator


