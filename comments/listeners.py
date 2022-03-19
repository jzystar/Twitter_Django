from utils.redis_helper import RedisHelper

def incr_comments_count(sender, instance, created, **kwargs):
    from django.db.models import F
    from tweets.models import Tweet

    if not created:
        return

    # .update will not trigger post_save listener
    # update count in Tweet table
    Tweet.objects.filter(id=instance.tweet_id).update(comments_count=F('comments_count') + 1)
    # update count in redis
    RedisHelper.incr_count(instance.tweet, 'comments_count')

def decr_comments_count(sender, instance, **kwargs):
    from django.db.models import F
    from tweets.models import Tweet

    # .update will not trigger post_save listener
    # update count in Tweet table
    Tweet.objects.filter(id=instance.tweet_id).update(comments_count=F('comments_count') - 1)
    # update count in redis
    RedisHelper.decr_count(instance.tweet, 'comments_count')