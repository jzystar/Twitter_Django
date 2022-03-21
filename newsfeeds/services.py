from newsfeeds.models import NewsFeed
from newsfeeds.tasks import fanout_newsfeeds_tasks
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper


class NewsFeedService:
    
    @classmethod
    def fanout_to_followers(cls, tweet):
        # cannot pass tweet as parameter because celery doesn't know how to serialize Tweet obj
        fanout_newsfeeds_tasks.delay(tweet.id) # .delay => asynchronously
        # fanout_newsfeeds_tasks(tweet.id)  # .delay => synchronously

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        # queryset is lazy-loading
        queryset = NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)

        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        # queryset is lazy-loading
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)

        return RedisHelper.push_object(key, newsfeed, queryset)