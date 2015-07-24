from .serializers import *
from drf_cached_instances.cache import BaseCache
from rest_framework.request import Request
from django.test.client import RequestFactory

def get_default_loader(model_class):

    def default_loader(self, pk):
        try:
            obj = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            return None
        return obj
    return default_loader


def get_default_invalidator(model_class):
    # never invalidates, cache is refreshed on reboot only
    return lambda x: []

def get_default_serializer_class(model_class):
    ClassName = model_class.__name__
    class_name = ClassName.lower()

    # a dummy request to create the serializer class
    request = Request(RequestFactory().get('/v1/' + class_name + '/'))

    # assume standard serializer name
    serializer_name = ClassName + 'Serializer'
    assert serializer_name in globals()
    return lambda x: globals()[serializer_name](context={'request': request})

def get_cache_class(model_class):
    """
    Returns a default cache class for a Model class.
    """

    ClassName = model_class.__name__
    class_name = ClassName.lower()
    cache_class = type(ClassName + "Cache", (BaseCache,), {class_name + '_default_loader': get_default_loader(model_class),
                                                    class_name + '_default_invalidator': get_default_invalidator(model_class),
                                                    class_name + '_default_serializer_class': get_default_serializer_class(model_class)})
    print(class_name + '_default_loader is ' + str(getattr(cache_class, class_name + '_default_loader')))
    print(class_name + '_default_invalidator is ' + str(getattr(cache_class, class_name + '_default_invalidator')))
    print(class_name + '_default_serializer_class is ' + str(getattr(cache_class, class_name + '_default_serializer_class')))
    return cache_class
