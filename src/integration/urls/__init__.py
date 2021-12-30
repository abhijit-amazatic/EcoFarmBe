"""
URL Configuration
"""
from django.conf.urls import url, include
from django.urls import path
from rest_framework.routers import SimpleRouter

from ..views import (
    GetBoxTokensView,
    GetBoxSharedLink,
    TemplateSignView,
    GetDistanceView,
    GetTemplateStatus,
    GetBoxTokenAuthenticationView,
    GetNewsFeedView,
    GetAutoComplete,
    NotificationView,
    DownloadSignDocumentView,
    CampaignView,
    ChatbotView,
    ConfiaCallbackView,
    AgrementBoxSignViewSet,
)

from . import (
     books_urls,
     crm_urls,
)
app_name = "integration"

router = SimpleRouter()
router.register(r'box/sign/agreement', AgrementBoxSignViewSet, base_name="box-sign-agreement")

urlpatterns = [
    path(r'crm/', include(crm_urls, namespace='crm')),
    path(r'books/', include(books_urls, namespace='books')),

    path(r'box/link/', GetBoxSharedLink.as_view(), name='get_shared_link'),
    path(r'integration/box/', GetBoxTokensView.as_view(), name='box'),
    path(r'integration/box-aws/', GetBoxTokenAuthenticationView.as_view(), name='box-token-authentication'),
    path(r'integration/distance/', GetDistanceView.as_view(), name='get_distance'),
    path(r'integration/confia/callback/', ConfiaCallbackView.as_view(), name="confia-callback"),
    path(r'sign/template/', TemplateSignView.as_view(), name='sign_template'),
    path(r'sign/template-status/', GetTemplateStatus.as_view(), name='template_status'),
    path(r'sign/download/', DownloadSignDocumentView.as_view(), name="download-sign-document"),
    path(r'notify/', NotificationView.as_view(), name='notification'),
    path(r'news/', GetNewsFeedView.as_view(), name='news-feed'),
    path(r'autocomplete/', GetAutoComplete.as_view(), name="address-autocomplete"),
    path(r'campaign/', CampaignView.as_view(), name="campaign"),
    path(r'bot/', ChatbotView.as_view(), name="chat-bot"),
] + router.urls
