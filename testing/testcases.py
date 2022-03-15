from comments.models import Comment
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.test import TestCase as DjangoTestCase
from likes.models import Like
from newsfeeds.models import NewsFeed
from rest_framework.test import APIClient
from tweets.models import Tweet
from utils.redis_client import RedisClient


class TestCase(DjangoTestCase):

    def clear_cache(self):
        RedisClient.clear()
        caches['testing'].clear()

    @property
    def anonymous_user(self):
        if hasattr(self, '_anonymous_user'):
            return self._anonymous_user
        self._anonymous_user = APIClient()
        return self._anonymous_user

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = 'generic password'
        if email is None:
            email = f'{username}@twitter.com'

        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'

        return Tweet.objects.create(user=user, content=content)

    def create_comment(self, user, tweet, content=None):
        if content is None:
            content = 'default comment content'

        return Comment.objects.create(user=user, tweet=tweet, content=content)

    def create_newsfeed(self, user, tweet):
        return NewsFeed.objects.create(user=user, tweet=tweet)


    def create_like(self, user, target):
        instance, _ = Like.objects.get_or_create(
            object_id=target.id,
            content_type=ContentType.objects.get_for_model(target.__class__),
            user=user
        )
        return instance