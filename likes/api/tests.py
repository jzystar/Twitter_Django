from testing.testcases import TestCase
from rest_framework.test import APIClient
from likes.models import Like


LIKE_BASE_URL = '/api/likes/'


class LikeApiTest(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_tweet_likes(self):
        tweet = self.create_tweet(self.user1)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        # must log in to like a tweet
        response = self.anonymous_user.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # wrong content_type
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'twet',
            'object_id': tweet.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # wrong object_id
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': 0
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # get is not allowed
        response = self.user1_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # post successfully
        response = self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)

        # duplicated likes
        self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.user2_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 2)

    def test_comment_likes(self):
        tweet = self.create_tweet(self.user1)
        comment = self.create_comment(self.user2, tweet)
        data = {'content_type': 'comment', 'object_id': comment.id}

        # must log in to like a tweet
        response = self.anonymous_user.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # wrong content_type
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'coment',
            'object_id': comment.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # wrong object_id
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': 0
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # get is not allowed
        response = self.user1_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # post successfully
        response = self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)

        # duplicated likes
        self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 1)
        self.user2_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)