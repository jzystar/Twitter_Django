from testing.testcases import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from tweets.models import Tweet
from datetime import timedelta
from utils.time_helpers import utc_now
from tweets.models import TweetPhoto
from tweets.constants import TweetPhotoStatus


class TweetTests(TestCase):

    def setUp(self):
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