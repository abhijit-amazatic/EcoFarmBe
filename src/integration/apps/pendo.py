"""
BCC license library.
"""
import json
import time
import requests
from datetime import (datetime, )
from core.settings import (TRACK_EVENT_SECRET_KEY,)

def send_track_event(event_name,visitor_id,properties):
    """
    Post track event to pendo.
    """
    url = "https://app.pendo.io/data/track"
    headers = dict()
    headers['x-pendo-integration-key'] = TRACK_EVENT_SECRET_KEY
    headers['Content-Type'] = "application/json"
    data_dict = {
        "type": "track",
        "event": event_name,
        "visitorId": visitor_id,
        "timestamp": int(time.time() * 1000),
        "properties": properties,
    }
    payload = data_dict 
    response = requests.request("POST", url, data=payload, headers=headers)
    return response.json()
