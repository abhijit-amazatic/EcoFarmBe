import json
from .models import (Integration, )
from core.settings import (
    CAMPAIGN_CLIENT_ID,
    CAMPAIGN_CLIENT_SECRET,
    CAMPAIGN_REFRESH_TOKEN,
    CAMPAIGN_REDIRECT_URI,
)
from pyzoho.campaign import Campaign

def get_campaign_obj():
    """
    Return pyzoho.campaign object.
    """
    try:
        token = Integration.objects.get(name='campaign')
        access_token = token.access_token
        access_expiry = token.access_expiry
        refresh_token = token.refresh_token
    except Integration.DoesNotExist:
        access_token = access_expiry = None
        refresh_token = CAMPAIGN_REFRESH_TOKEN
    campaign = Campaign(
        client_id=CAMPAIGN_CLIENT_ID,
        client_secret=CAMPAIGN_CLIENT_SECRET,
        refresh_token=refresh_token,
        redirect_uri=CAMPAIGN_REDIRECT_URI,
        access_token=access_token,
        access_expiry=access_expiry,
    )
    if campaign.refreshed:
        Integration.objects.update_or_create(
            name='campaign',
            defaults={
                "name": 'campaign',
                "client_id":campaign.CLIENT_ID,
                "client_secret":campaign.CLIENT_SECRET,
                "access_token":campaign.ACCESS_TOKEN,
                "access_expiry":campaign.ACCESS_EXPIRY[0],
                "refresh_token":campaign.REFRESH_TOKEN
                }
        )
    return campaign

def create_campaign(campaign_name, from_email, campaign_subject, list_details, content_url, params={}):
    """
    Create campaign in the Zoho Campaign.
    """
    campaign = get_campaign_obj()
    list_details = json.dumps(list_details)
    return campaign.create_campaign(campaign_name, from_email, campaign_subject, list_details, content_url, params)