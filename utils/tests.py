from testing.testcases import TestCase
from utils.redis_client import RedisClient


class UtilsTest(TestCase):

    def test_redis_client(self):
        conn = RedisClient.get_connection()
        conn.lpush('test_key', 1)
        conn.lpush('test_key', 2)
        cached_list = conn.lrange('test_key', 0, -1)
        self.assertEqual(cached_list, [b'2', b'1'])

        # clear cache
        RedisClient.clear()
        cached_list = conn.lrange('test_key', 0, -1)
        self.assertEqual(cached_list, [])
