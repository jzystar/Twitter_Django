from django.conf import settings
import redis


class RedisClient:
    conn = None # use instance variable to avoid reconnecting redis

    @classmethod
    def get_connection(cls):
        if cls.conn is not None:
            return cls.conn

        cls.conn = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )

        return cls.conn

    @classmethod
    def clear(cls):
        # clear all keys in redis, for testing purpose
        if not settings.TESTING:
            raise Exception("You can not flush redis in production environment")
        conn = cls.get_connection()
        conn.flushdb()
