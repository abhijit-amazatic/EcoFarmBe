"""
Provides common resuable Model related functionality throughout the project
"""

from collections import namedtuple
from django.utils import timezone
from django.db.models import Q


def chunk(lst, count=500):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(lst), count):
        yield lst[i:i + count]
        
   
def _batch_create_update(model, keys, lookup_keys, items, ignore_update=False):
    """
    An internal generic function to smartly and efficiently bulk create or update a list of
    model objects specified as items. This one doesn't use chunking.
    """
    key_class = namedtuple("DictKey", lookup_keys)

    # create list of items for filtering
    filter_q = Q()
    for item in items:
        filter_q = filter_q | Q(**{key: item[key] for key in lookup_keys})

    # filter items
    item_details = {}
    for item in model.objects.filter(filter_q):
        item_key = {key: getattr(item, key) for key in lookup_keys}
        item_details[key_class(**item_key)] = item

    bulk_creation, keep_ids = [], []
    update_keys = list(set(keys) - set(lookup_keys))

    for item in items:
        item_key = {key: item[key] for key in lookup_keys}
        item_in_db = item_details.get(key_class(**item_key))
        if item_in_db:
            keep_ids.append(item_in_db.pk)
            if not ignore_update:
                for key in update_keys:
                    if item[key] != getattr(item_in_db, key):
                        model.objects.filter(pk=item_in_db.pk).update(
                            **{key: item[key] for key in update_keys})
                        break
        else:
            bulk_creation.append(model(**{key: item[key] for key in keys}))

    return bulk_creation, keep_ids


def batch_create_update(model, keys, lookup_keys, items, bulk_remove_filter=None, batch_size=500, ignore_update=False):
    """
    A generic function to smartly and efficiently bulk create or update a list of
    model objects specified as items in chunks.
    """
    all_bulk_creation, all_keep_ids = [], []
    for _items in chunk(items, batch_size):
        bulk_creation, keep_ids = _batch_create_update(
            model, keys, lookup_keys, _items, ignore_update=ignore_update)
        all_bulk_creation += bulk_creation
        all_keep_ids += keep_ids

    if bulk_remove_filter is not None:
        _previous_items = []
        for _items in chunk(sorted(all_keep_ids), batch_size):
            if not _items:
                continue
            _item_filter = {'id__lte': _items[
                len(_items) - 1]} if _items else {}
            if _previous_items:
                _item_filter['id__gt'] = _previous_items[
                    len(_previous_items) - 1]
            _item_filter.update(bulk_remove_filter)
            model.objects.exclude(id__in=_items).filter(
                **_item_filter).delete()
            _previous_items = _items
        if _previous_items:
            _item_filter = {'id__gt': _previous_items[
                len(_previous_items) - 1]}
            _item_filter.update(bulk_remove_filter)
            model.objects.filter(**_item_filter).delete()

    model.objects.bulk_create(all_bulk_creation, batch_size=batch_size)
