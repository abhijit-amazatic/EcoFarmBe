import time
import threading
from django.conf import settings


from .box import get_box_client
from.tasks import box_sign_update_to_db_task
from .models import (
    BoxSign,
    BoxEventTracker,
)
TRACKER_THREAD_NAME = 'box_sign_event_tracker'

class BoxSignEventTracker(threading.Thread):
    BOX_SIGN_EVENT_TRACKING_INTERVAL = 2
    event_types = [
        # 'SIGN_DOCUMENT_ASSIGNED',
        'SIGN_DOCUMENT_CANCELLED',
        'SIGN_DOCUMENT_COMPLETED',
        # 'SIGN_DOCUMENT_CONVERTED',
        # 'SIGN_DOCUMENT_CREATED',
        'SIGN_DOCUMENT_DECLINED',
        'SIGN_DOCUMENT_EXPIRED',
        'SIGN_DOCUMENT_SIGNED',
        # 'SIGN_DOCUMENT_VIEWED_BY_SIGNER',
        # 'SIGNER_DOWNLOADED',
        # 'SIGNER_FORWARDED',
    ]

    def __init__(self):
        super().__init__()
        if hasattr(settings, 'BOX_SIGN_EVENT_TRACKING_INTERVAL'):
            self.BOX_SIGN_EVENT_TRACKING_INTERVAL = settings.BOX_SIGN_EVENT_TRACKING_INTERVAL
            if self.BOX_SIGN_EVENT_TRACKING_INTERVAL < 1:
                raise Exception("""Value of BOX_SIGN_EVENT_TRACKING_INTERVAL must be greater than 0.""")
        self.client = get_box_client()
        self.model_obj, _ = BoxEventTracker.objects.get_or_create(id='box_sign')

    def run(self):
        print("******* Box Sign Event Tracker Started.")
        while True:
            time.sleep(self.BOX_SIGN_EVENT_TRACKING_INTERVAL)
            try:
                self.process_events()
            except Exception as e:
                print(e)

    def process_events(self):
        events = self.client.events()
        self.model_obj.refresh_from_db()
        if self.model_obj.is_state_ideal:
            self.model_obj.is_state_ideal = False
            self.model_obj.save()
            events_stream = events.get_admin_events_streaming(
                event_types=self.event_types,
                stream_position=self.model_obj.stream_position
            )
            self.model_obj.stream_position = events_stream['next_stream_position']
            self.model_obj.is_state_ideal = True
            self.model_obj.save()
            file_id_ls = []
            for event in events_stream['entries']:
                files = event.additional_details.get('sign_request', {}).get('files')
                print(f'Event {event.event_type}: {files} at {event.created_at}')

                file_id_ls += [f.id for f  in files]

            if file_id_ls:
                for obj in BoxSign.objects.filter(output_file_id__in=file_id_ls).distinct():
                    box_sign_update_to_db_task.delay(obj.id)

def start_tracking():
    already_exists = False

    for t in threading.enumerate():
        if t.getName() == TRACKER_THREAD_NAME:
            already_exists = True

    if not already_exists:
        t = BoxSignEventTracker()
        t.daemon = True
        t.setName(TRACKER_THREAD_NAME)
        t.start()

def test():
    t = BoxSignEventTracker()
    t.run()
