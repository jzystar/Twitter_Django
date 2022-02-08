from testing.testcases import TestCase
from rest_framework.test import APIClient
from notifications.models import Notification


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'
UNREAD_URL = '/api/notifications/unread-count/'
MARK_ALL_AS_READ_URL = '/api/notifications/mark-all-as-read/'
UPDATE_NOTIFICATION_URL = '/api/notifications/{}/'


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
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        # create comment
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'ajknjbbha',
        })
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 2)

        # user2 cannot see the notifications
        response = self.user2_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 0)

    def test_mark_as_read(self):
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
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 2)

        # GET not allowed
        response = self.user1_client.get(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 405)

        # anonymous not allowed
        response = self.anonymous_user.post(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 403)

        # user2 cannot see any notifications
        response = self.user2_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 0)

        # user1 post is allowed, mark all as read
        response = self.user1_client.post(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        response = self.user1_client.get(UNREAD_URL)
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

    def test_update(self):
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

        notification = Notification.objects.filter(recipient=self.user1.id).first()
        url = UPDATE_NOTIFICATION_URL.format(notification.id)
        # post is not allowed
        response = self.user1_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, 405)

        # must log in
        response = self.anonymous_user.put(url, {'unread': False})
        self.assertEqual(response.status_code, 403)

        # other users cannot mark as read
        response = self.user2_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)

        # mark to be read successfully
        response = self.user1_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 1)

        # mark to be unread successfully
        response = self.user1_client.put(url, {'unread': True})
        self.assertEqual(response.status_code, 200)
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 2)

        # must hava unread parameter
        response = self.user1_client.put(url)
        self.assertEqual(response.status_code, 400)

        # cannot update other info except read/unread
        response = self.user1_client.put(url, {'unread': False, 'verb': 'newverb'})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db() #refresh memory
        self.assertNotEqual(notification.verb, 'newverb')