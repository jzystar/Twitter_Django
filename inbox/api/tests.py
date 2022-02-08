from testing.testcases import TestCase
from rest_framework.test import APIClient
from notifications.models import Notification


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'


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

class NotificationApiTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_unread_count(self):
        tweet = self.create_tweet(self.user1)
        # create like
        self.user2_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': tweet.id
        })
        url = '/api/notifications/unread-count/'
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        # create comment
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'ajknjbbha',
        })
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 2)

        # user2 cannot see the notifications
        response = self.user2_client.get(url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_mark_as_read(self):
        tweet = self.create_tweet(self.user1)
        # create like
        self.user2_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': tweet.id
        })
        unread_url = '/api/notifications/unread-count/'
        # create comment
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'ajknjbbha',
        })
        response = self.user1_client.get(unread_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 2)

        mark_url = '/api/notifications/mark-all-as-read/'
        # GET not allowed
        response = self.user1_client.get(mark_url)
        self.assertEqual(response.status_code, 405)

        # anonymous not allowed
        response = self.anonymous_user.post(mark_url)
        self.assertEqual(response.status_code, 403)

        # user2 cannot see any notifications
        response = self.user2_client.get(unread_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 0)

        # user1 post is allowed, mark all as read
        response = self.user1_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        response = self.user1_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        tweet = self.create_tweet(self.user1)
        # create like
        self.user2_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': tweet.id
        })
        # create comment
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'ajknjbbha',
        })

        # anonymous not allowed
        response = self.anonymous_user.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 403)

        # user2 cannot see any notifications
        response = self.user2_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        # user1 can see notifications
        response = self.user1_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

        # mark 1 as read
        notification = Notification.objects.filter(recipient=self.user1).first()
        notification.unread = False
        notification.save()
        response = self.user1_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

        response = self.user1_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        response = self.user1_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)