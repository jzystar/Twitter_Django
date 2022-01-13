from testing.testcases import TestCase
from rest_framework.test import APIClient


COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):
    
    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)
        self.tweet = self.create_tweet(self.user1)
        
        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)
        
    def test_create(self):
        # have to log in
        response = self.anonymous_user.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)
        
        # no parameter
        response = self.user1_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)
        
        # only have tweet_id
        response = self.user1_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        # only have content
        response = self.user1_client.post(COMMENT_URL, {'content': 'Hello'})
        self.assertEqual(response.status_code, 400)

        # content too long
        response = self.user1_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1'*141
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)

        # comment successfully
        response = self.user1_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id, 'content': '1'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')