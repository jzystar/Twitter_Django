from testing.testcases import TestCase
from rest_framework.test import APIClient
from tweets.models import Tweet


TWEET_LIST_API = '/api/tweets/' # must end with /
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'


class TweetApiTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user('user1', 'user1@gmail.com')
        # create 3 tweets
        self.tweets1 = [self.create_tweet(self.user1) for _ in range(3)]
        self.user1_client = APIClient()
        # forcibly authenticate a request
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2', 'user2@gmail.com')
        self.tweets2 = [self.create_tweet(self.user2) for _ in range(2)]
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_list_api(self):
        # no user_id
        response = self.anonymous_user.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        # correct request for user1
        response = self.anonymous_user.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), 3)

        # correct request for user2
        response = self.anonymous_user.get(TWEET_LIST_API, {'user_id': self.user2.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), 2)
        # check the order
        self.assertEqual(response.data['tweets'][0]['id'], self.tweets2[1].id)
        self.assertEqual(response.data['tweets'][1]['id'], self.tweets2[0].id)

    def test_create_api(self):
        # not logged in
        response = self.anonymous_user.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 403)

        # no content
        response = self.user1_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 400)
        # short content
        response = self.user1_client.post(TWEET_CREATE_API, {'content': '1'})
        self.assertEqual(response.status_code, 400)
        # long content
        response = self.user1_client.post(TWEET_CREATE_API, {'content': '1'*141})
        self.assertEqual(response.status_code, 400)

        # correct post
        tweets_count = Tweet.objects.count()
        response = self.user1_client.post(TWEET_CREATE_API, {'content': 'Hello world!'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Tweet.objects.count(), tweets_count + 1)
    
    def test_retrieve(self):
        # wrong tweet id 
        url = TWEET_RETRIEVE_API.format(0)
        response = self.anonymous_user.get(url)
        self.assertEqual(response.status_code, 404)
        
        # get all comments
        tweet = self.create_tweet(self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)
        response = self.anonymous_user.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # add comments
        self.create_comment(self.user1, tweet)
        self.create_comment(self.user2, tweet)
        another_tweet = self.create_tweet(self.user2)
        self.create_comment(self.user1, another_tweet)
        response = self.anonymous_user.get(url)
        self.assertEqual(len(response.data['comments']), 2)