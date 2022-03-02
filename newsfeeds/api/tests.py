from testing.testcases import TestCase
from tweets.models import Tweet
from friendships.models import Friendship
from rest_framework.test import APIClient
from utils.paginations import EndlessPagination


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
        self.assertEqual(len(response.data['results']), 0)
        # self post a tweet
        self.user1_client.post(POST_TWEETS_URL, {'content': "hello world."})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tweet']['user']['id'], self.user1.id)
        # follow user2, and user2 post a tweet
        self.user1_client.post(FOLLOW_URL.format(self.user2.id))
        response = self.user2_client.post(POST_TWEETS_URL, {'content': 'hello LA!'})
        posted_tweet_id = response.data['id'] # check id match
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_endless_pagination(self):
        page_size = EndlessPagination.page_size
        newsfeeds = []
        for i in range(page_size * 2):
            tweet = self.create_tweet(self.user1, 'tweet{}'.format(i))
            newsfeed = self.create_newsfeed(self.user1, tweet)
            newsfeeds.append(newsfeed)
        newsfeeds = newsfeeds[::-1]

        # pull the 1st page
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[page_size - 1].id)

        # pull the 2nd page
        response = self.user1_client.get(NEWSFEEDS_URL, {
            'created_at__lt':newsfeeds[page_size - 1].created_at
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[page_size + 1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[2 * page_size - 1].id)

        # pull the latest newsfeeds
        response = self.user1_client.get(NEWSFEEDS_URL, {
            'created_at__gt': newsfeeds[0].created_at
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)
        # add a new newsfeed
        new_tweet = self.create_tweet(self.user1)
        newsfeed = self.create_newsfeed(self.user1, new_tweet)
        response = self.user1_client.get(NEWSFEEDS_URL, {
            'created_at__gt': newsfeeds[0].created_at
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], newsfeed.id)