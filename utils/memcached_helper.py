from django.conf import settings
from django.core.cache import caches

cache = caches['testing'] if settings.TESTING else caches['default']


class MemcachedHelper:

    @classmethod
    def get_key(cls, model_class, object_id):
        # model_class.__class__.__name__ to get class name, Tweet =>'Tweet', User=>'User'
        return '{}:{}'.format(model_class.__class__.__name__, object_id)

    @classmethod
    def get_object_through_cache(cls, model_class, object_id):
        key = cls.get_key(model_class, object_id)
        obj = cache.get(key) # cache hit
        if obj is not None:
            return obj

        obj = model_class.objects.get(id=object_id) # cache miss
        cache.set(key, obj)
        return obj

    @classmethod
    def invalidate_cached_object(cls, model_class, object_id):
        key = cls.get_key(model_class, object_id)
        cache.delete(key)