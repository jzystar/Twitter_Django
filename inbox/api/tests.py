from testing.testcases import TestCase
from rest_framework.test import APIClient
from notifications.models import Notification


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'

class NotificationTestCase(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_comment_create_api_trigger_notification(self):
        tweet = self.create_tweet(self.user1)
        # tweet owner comment himself
        self.user1_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'ajknjbbha',
        })
        self.assertEqual(Notification.objects.count(), 0)
        # other user comment
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'ajknjbbha',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        tweet = self.create_tweet(self.user1)
        # tweet owner like his tweet, no notification
        self.user1_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': tweet.id
        })
        self.assertEqual(Notification.objects.count(), 0)
        # other user like this tweet
        self.user2_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': tweet.id
        })
        self.assertEqual(Notification.objects.count(), 1)