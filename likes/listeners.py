from utils.redis_helper import RedisHelper

def incr_likes_count(sender, instance, created, **kwargs):
    from django.db.models import F
    from comments.models import Comment
    from tweets.models import Tweet
    # only creating new likes will update likes_count
    if not created:
        return

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        Comment.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)
        RedisHelper.incr_count(instance.content_object, 'likes_count')
        return

    # F has row lock to solve concurrent issues (many likes at the same time).
    # .update will not trigger post_save listener
    # update count in Tweet table
    Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)
    # update count in redis
    RedisHelper.incr_count(instance.content_object, 'likes_count')

def decr_likes_count(sender, instance, **kwargs):
    from django.db.models import F
    from comments.models import Comment
    from tweets.models import Tweet

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        Comment.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
        RedisHelper.decr_count(instance.content_object, 'likes_count')
        return

    # F has row lock to solve concurrent issues (many likes at the same time).
    # .update will not trigger post_save listener
    # update count in Tweet table
    Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
    # update count in redis
    RedisHelper.decr_count(instance.content_object, 'likes_count')