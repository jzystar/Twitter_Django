from django.test import TestCase
from django.contrib.auth.models import User
from tweets.models import Tweet
from datetime import timedelta
from utils.time_helpers import utc_now


class TweetTests(TestCase):

    def test_hour_to_now(self):
        xxx_user = User.objects.create_user(username='testuser')
        tweet = Tweet.objects.create(user=xxx_user, content="always have good luck")
        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()
        self.assertEqual(tweet.hours_to_now, 10)