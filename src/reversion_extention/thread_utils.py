from collections import namedtuple
from threading import local

_SeralizedInstances = namedtuple("SeralizedInstances", (
    "format",
    "seralized_data",
))

_ObjInfo = namedtuple("ObjInfo", (
    "content_type_id",
    "object_id",
    "verbose_name",
    "obj_name",
))


# class _Local(local):

#     def __init__(self):
#         self.seralized_instances = ()
#         self.deleted_obj_info = ()
#         self.created_obj_info = ()

_local = local()

def initiate_local():
    _local.seralized_instances = ()
    _local.deleted_obj_info = ()
    _local.created_obj_info = ()

def get_seralized_instances():
    if hasattr(_local, 'seralized_instances'):
        return tuple((i.format, i.seralized_data) for i in _local.seralized_instances)
    else:
        return ()

def push_seralized_instances(format, seralized_data):
    seralized_instance = _SeralizedInstances(
        format=format,
        seralized_data=seralized_data,
    )
    if hasattr(_local, 'seralized_instances'):
        _local.seralized_instances += (seralized_instance,)
    else:
        _local.seralized_instances = (seralized_instance,)



def get_deleted_obj_info():
    if hasattr(_local, 'deleted_obj_info'):
        return _local.deleted_obj_info
    else:
        return ()

def push_deleted_obj_info(content_type_id, object_id, verbose_name, obj_name):
    obj_info = _ObjInfo(
        content_type_id=content_type_id,
        object_id=object_id,
        verbose_name=verbose_name,
        obj_name=obj_name,
    )
    if hasattr(_local, 'deleted_obj_info'):
        _local.deleted_obj_info += (obj_info,)
    else:
        _local.deleted_obj_info = (obj_info,)


def get_created_obj_info():
    if hasattr(_local, 'created_obj_info'):
        return _local.created_obj_info
    else:
        return ()

def push_created_obj_info(content_type_id, object_id, verbose_name, obj_name):
    obj_info = _ObjInfo(
        content_type_id=content_type_id,
        object_id=object_id,
        verbose_name=verbose_name,
        obj_name=obj_name,
    )
    if hasattr(_local, 'created_obj_info'):
        _local.created_obj_info += (obj_info,)
    else:
        _local.created_obj_info = (obj_info,)

