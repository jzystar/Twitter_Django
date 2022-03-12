from datetime import timedelta
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import Tweet
from tweets.models import TweetPhoto
from utils.redis_client import RedisClient
from utils.time_helpers import utc_now
from utils.redis_serializers import DjangoModelSerializer


class TweetTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('testuser1')
        self.tweet = self.create_tweet(self.user1)
        self.user_client1 = APIClient()
        self.user_client1.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user_client2 = APIClient()
        self.user_client2.force_authenticate(self.user2)

    def test_hour_to_now(self):
        xxx_user = User.objects.create_user(username='testuser')
        tweet = Tweet.objects.create(user=xxx_user, content="always have good luck")
        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()
        self.assertEqual(tweet.hours_to_now, 10)

    def test_like_set(self):
        self.assertEqual(self.tweet.like_set.count(), 0)
        self.create_like(self.user2, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

    def test_upload_picture(self):
        photo = TweetPhoto.objects.create(user=self.user1, tweet=self.tweet)
        self.assertEqual(photo.user.id, self.user1.id)
        self.assertEqual(photo.status, TweetPhotoStatus.PENDING)
        self.assertEqual(TweetPhoto.objects.count(), 1)

    def test_cache_tweet_in_redis(self):
        tweet = self.create_tweet(self.user1)
        conn = RedisClient.get_connection()
        serialized_data = DjangoModelSerializer.serialize(tweet)
        key = 'tweet:{}'.format((tweet.id))
        conn.set(key, serialized_data)

        data = conn.get('wrong_key')
        self.assertEqual(data, None)

        data = conn.get(key)
        cached_tweet = DjangoModelSerializer.deserialize(data)
        self.assertEqual(tweet, cached_tweet)