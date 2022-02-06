from testing.testcases import TestCase
from rest_framework.test import APIClient
from inbox.services import NotificationService
from notifications.models import Notification


class NotificationServiceTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_send_comment_notification(self):
        # tweet owner comment his tweet, no notification
        tweet = self.create_tweet(self.user1)
        comment = self.create_comment(self.user1, tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        # different user comment, there is a notification
        comment = self.create_comment(self.user2, tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notification(self):
        # tweet owner like his tweet, no notification
        tweet = self.create_tweet(self.user1)
        like = self.create_like(self.user1, tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        # different user like the tweet, there's notification
        like = self.create_like(self.user2, tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)