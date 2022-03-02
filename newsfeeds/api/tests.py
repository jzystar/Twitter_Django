from testing.testcases import TestCase
from tweets.models import Tweet
from friendships.models import Friendship
from rest_framework.test import APIClient


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTest(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

        #

    def test_list(self):
        # has to log in
        response = self.anonymous_user.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)
        # cannot use post
        response = self.user1_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)
        # use get, success
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 0)
        # self post a tweet
        self.user1_client.post(POST_TWEETS_URL, {'content': "hello world."})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 1)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['user']['id'], self.user1.id)
        # follow user2, and user2 post a tweet
        self.user1_client.post(FOLLOW_URL.format(self.user2.id))
        response = self.user2_client.post(POST_TWEETS_URL, {'content': 'hello LA!'})
        posted_tweet_id = response.data['id'] # check id match
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)