from .models import School
from .serializers import SchoolSerializer
from drf_cached_instances.cache import BaseCache
from rest_framework.request import Request
from django.test.client import RequestFactory

class SchoolCache(BaseCache):

    """
    Caches school instances.
    """

    # a dummy school request to initialize the serializer
    request = Request(RequestFactory().get('/v1/school/'))

    def school_default_serializer(self, obj):
        ret = SchoolSerializer(context={'request': self.request}).to_representation(obj)
        from pprint import pprint
        pprint(ret)
        return ret

    def school_default_loader(self, pk):
        try:
            obj = School.objects.get(pk=pk)
        except School.DoesNotExist:
            return None
        return obj

    def school_default_invalidator(self, obj):
        # never invalidates, cache is refreshed on reboot only
        return []
