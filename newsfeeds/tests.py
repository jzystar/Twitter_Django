from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from newsfeeds.tasks import fanout_newsfeeds_main_task
from testing.testcases import TestCase
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_client import RedisClient


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('testuser1')
        self.user2 = self.create_user('testuser2')

    def test_cached_newsfeed_list_in_redis(self):
        newsfeed_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.user1, 'content:{}'.format(i))
            newsfeed = self.create_newsfeed(self.user2, tweet)
            newsfeed_ids.append(newsfeed.id)
        newsfeed_ids = newsfeed_ids[::-1]

        # create_tweet/create_newsfeed will push tweet/newsfeed to redis, clear!
        RedisClient.clear()
        conn = RedisClient.get_connection()

        # cache miss
        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.user2.id)
        self.assertEqual(conn.exists(key), False)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user2.id)
        self.assertEqual([newsfeed.id for newsfeed in newsfeeds], newsfeed_ids)

        # cache hit
        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.user2.id)
        self.assertEqual(conn.exists(key), True)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user2.id)
        self.assertEqual([newsfeed.id for newsfeed in newsfeeds], newsfeed_ids)

        # cache updated
        new_tweet = self.create_tweet(self.user1)
        new_newsfeed = self.create_newsfeed(self.user2, new_tweet)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user2.id)
        newsfeed_ids.insert(0, new_newsfeed.id)
        self.assertEqual([newsfeed.id for newsfeed in newsfeeds], newsfeed_ids)

        # username updated
        self.user2.username = "new_username"
        self.user2.save()
        self.assertEqual(newsfeeds[0].user.username, "new_username")

class NewsFeedTaskTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('testuser1')
        self.user2 = self.create_user('testuser2')

    def test_fanout_main_task(self):
        tweet = self.create_tweet(self.user1)
        self.create_friendship(self.user2, self.user1)
        msg = fanout_newsfeeds_main_task(tweet.id, self.user1.id)
        self.assertEqual(msg, '1 newsfeeds will be fanned out, 1 batches created')
        self.assertEqual(NewsFeed.objects.count(), 2)
        cached_list = NewsFeedService.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.create_user('user{}'.format(i))
            self.create_friendship(user, self.user1)
        tweet = self.create_tweet(self.user1)
        msg = fanout_newsfeeds_main_task(tweet.id, self.user1.id)
        # 3 followers now, fanout batch size = 3 if TESTING
        self.assertEqual(msg,'3 newsfeeds will be fanned out, 1 batches created')
        self.assertEqual(NewsFeed.objects.count(), 6)
        cached_list = NewsFeedService.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_list), 2)

        another_user = self.create_user('another user')
        self.create_friendship(another_user, self.user1)
        tweet = self.create_tweet(self.user1)
        msg = fanout_newsfeeds_main_task(tweet.id, self.user1.id)
        # 4 followers now, fanout batch size = 3 if TESTING
        self.assertEqual(msg, '4 newsfeeds will be fanned out, 2 batches created')
        self.assertEqual(NewsFeed.objects.count(), 11)
        cached_list = NewsFeedService.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_list), 3)
        # user1 post 3 tweets, so user2 has 3 in newsfeeds
        cached_list = NewsFeedService.get_cached_newsfeeds(self.user2.id)
        self.assertEqual(len(cached_list), 3)