from datetime import timedelta
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import Tweet
from tweets.models import TweetPhoto
from tweets.services import TweetService
from twitter.cache import USER_TWEETS_PATTERN
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
from utils.time_helpers import utc_now


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

    def test_cached_tweet_in_redis(self):
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

    def test_cached_tweet_list_in_redis(self):
        user = self.create_user('user1')
        tweet_ids = []
        for i in range(3):
            tweet = self.create_tweet(user, 'tweet {}'.format(i))
            tweet_ids.append(tweet.id)
        tweet_ids = tweet_ids[::-1]

        RedisClient.clear()
        conn = RedisClient.get_connection()

        # cache miss
        key = USER_TWEETS_PATTERN.format(user_id=user.id)
        self.assertEqual(conn.exists(key), False)
        tweets = TweetService.get_cached_tweets(user.id)
        self.assertEqual([tweet.id for tweet in tweets], tweet_ids)

        # cache hit
        self.assertEqual(conn.exists(key), True)
        tweets = TweetService.get_cached_tweets(user.id)
        self.assertEqual([tweet.id for tweet in tweets], tweet_ids)

        # cache updated
        new_tweet = self.create_tweet(user, 'new tweet')
        tweets = TweetService.get_cached_tweets(user.id)
        tweet_ids.insert(0, new_tweet.id)
        self.assertEqual([tweet.id for tweet in tweets], tweet_ids)

        # username updated
        user.username = 'new_username'
        user.save()
        self.assertEqual(tweets[0].user.username, 'new_username')