from utils.redis_client import RedisClient


class GateKeeper:

    @classmethod
    def get(cls, gk_name):
        conn = RedisClient.get_connection()
        name = 'gatekeeper:{}'.format(gk_name)
        if not conn.exists(name):
            return {'percent': 0, 'description': ''}

        redis_hashmap = conn.hgetall(name) # return a hashmap
        return {
            'percent': int(redis_hashmap.get(b'percent', 0)),
            'description': redis_hashmap.get(b'description', '')
        }

    @classmethod
    def set(cls, gk_name, key, value):
        conn = RedisClient.get_connection()
        name = 'gatekeeper:{}'.format(gk_name)
        conn.hset(name, key, value)

    @classmethod
    def is_switch_on(cls, gk_name):
        return cls.get(gk_name)['percent'] == 100

    @classmethod
    def is_in_gk(cls, gk_name, user_id):
        # if percent = 0, all user_id % 100 NOT < 0
        # if percent = 100, all user_id % 100 < 0
        return user_id % 100 < cls.get(gk_name)['percent']

