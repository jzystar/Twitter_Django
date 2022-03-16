from django.conf import settings
from friendships.models import Friendship
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet
from utils.paginations import EndlessPagination


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTest(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

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

    def test_cached_user_in_memcached(self):
        profile = self.user1.profile
        profile.nickname = 'user1'
        profile.save()
        
        self.assertEqual(self.user1.username, 'testuser1')
        self.assertEqual(self.user1.profile.nickname, 'user1')
        
        self.create_newsfeed(self.user1, self.create_tweet(self.user2))
        self.create_newsfeed(self.user1, self.create_tweet(self.user1))
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['user']['username'], 'testuser1')
        self.assertEqual(response.data['results'][0]['tweet']['user']['nickname'], 'user1')
        self.assertEqual(response.data['results'][1]['tweet']['user']['username'], 'testuser2')

        # update username or nickname
        self.user2.username = 'testuser2_new_username'
        self.user2.save()
        profile.nickname = 'user1_new_nickname'
        profile.save()
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['user']['username'], 'testuser1')
        self.assertEqual(response.data['results'][0]['tweet']['user']['nickname'], 'user1_new_nickname')
        self.assertEqual(response.data['results'][1]['tweet']['user']['username'], 'testuser2_new_username')

    def test_cached_tweet_in_memcached(self):
        tweet = self.create_tweet(self.user1, 'old content')
        self.create_newsfeed(self.user2, tweet)
        response = self.user2_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['user']['username'], 'testuser1')
        self.assertEqual(response.data['results'][0]['tweet']['content'], 'old content')

        # update username
        self.user1.username = 'newtestuser1'
        self.user1.save()
        response = self.user2_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['user']['username'], 'newtestuser1')

        # update content
        tweet.content = 'new content'
        tweet.save()
        response = self.user2_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['content'], 'new content')

    def _paginate_to_get_all_newsfeeds(self, client):
        response = client.get(NEWSFEEDS_URL)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = response.data['results'][-1]['created_at']
            response = client.get(NEWSFEEDS_URL, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])

        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = EndlessPagination.page_size
        users = [self.create_user('user{}'.format(i)) for i in range(5)]
        newsfeeds = []
        for i in range(list_limit + page_size):
            tweet = self.create_tweet(users[i % 5], 'content{}'.format(i))
            newsfeed = self.create_newsfeed(self.user1, tweet)
            newsfeeds.append(newsfeed)
        newsfeeds = newsfeeds[::-1]

        # only cache limited objects
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        queryset = NewsFeed.objects.filter(user=self.user1)
        self.assertEqual(queryset.count(), list_limit + page_size)

        results = self._paginate_to_get_all_newsfeeds(self.user1_client)
        self.assertEqual(len(results), list_limit + page_size)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].id, results[i]['id'])

        # a new follower publish a tweet
        new_tweet = self.create_tweet(self.user2, 'user2 publish a tweet')
        new_newsfeed = self.create_newsfeed(self.user1, new_tweet)
        newsfeeds.insert(0, new_newsfeed)
        def _test_newsfeeds_after_new_feed_pushed():
            results = self._paginate_to_get_all_newsfeeds(self.user1_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            for i in range(list_limit + page_size + 1):
                self.assertEqual(newsfeeds[i].id, results[i]['id'])

        _test_newsfeeds_after_new_feed_pushed()

        # cached expired
        self.clear_cache()
        _test_newsfeeds_after_new_feed_pushed()