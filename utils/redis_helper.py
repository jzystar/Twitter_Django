from django.conf import settings
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer


class RedisHelper:

    @classmethod
    def _load_objects_to_cache(cls, key, queryset):
        conn = RedisClient.get_connection()
        serialized_list = []
        # redis only save up to REDIS_LIST_LENGTH_LIMIT data
        for obj in queryset[:settings.REDIS_LIST_LENGTH_LIMIT]:
            serialized_data = DjangoModelSerializer.serialize(obj)
            serialized_list.append(serialized_data)

        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, key, queryset):
        conn = RedisClient.get_connection()
        if conn.exists(key):
            serialized_list = conn.lrange(key, 0, -1)
            objects = []
            for serialized_data in serialized_list:
                deserialized_obj = DjangoModelSerializer.deserialize(serialized_data)
                objects.append(deserialized_obj)
            return objects

        cls._load_objects_to_cache(key, queryset)

        return list(queryset)

    @classmethod
    def push_object(cls, key, obj, queryset):
        conn = RedisClient.get_connection()
        if not conn.exists(key):
            cls._load_objects_to_cache(key, queryset)
            return

        serialized_data = DjangoModelSerializer.serialize(obj)
        conn.lpush(key, serialized_data)
        # ensure redis only has up to settings.REDIS_LIST_LENGTH_LIMIT data
        conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)

    @classmethod
    def get_count_key(cls, obj, attr):
        return '{}.{}:{}'.format(obj.__class__.__name__, attr, obj.id)

    @classmethod
    def incr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if conn.exists(key):
            return conn.incr(key) # increase count by 1 and return

        # refresh from db, don't need to add 1 before set key value
        obj.refresh_from_db()
        conn.set(key, getattr(obj, attr)) # getattr(obj, attr) => tweet.likes_count
        conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
        return getattr(obj, attr)

    @classmethod
    def decr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if conn.exists(key):
            return conn.decr(key)

        # refresh from db, don't need to minus 1 before set key value
        obj.refresh_from_db()
        conn.set(key, getattr(obj, attr))  # getattr(obj, attr) => tweet.likes_count
        conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
        return getattr(obj, attr)

    @classmethod
    def get_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if conn.exists(key):
            return int(conn.get(key)) # use int(), otherwise, return b'1'

        obj.refresh_from_db()
        conn.set(key, getattr(obj, attr))
        return getattr(obj, attr)
