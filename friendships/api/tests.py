from friendships.api.paginations import FriendshipPagination
from friendships.models import Friendship
from friendships.services import FriendshipService
from gatekeeper.models import GateKeeper
from rest_framework.test import APIClient
from testing.testcases import TestCase

FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        # call superclass setup
        super(FriendshipApiTests, self).setUp()
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

        # create followings and followers for user2
        for i in range(2):
            follower = self.create_user("testuser2's followers{}".format(i))
            # call create_friendship to crate friendship in MySQL or HBase
            self.create_friendship(follower, self.user2)
        for i in range(3):
            following = self.create_user("testuser2's followings{}".format(i))
            self.create_friendship(self.user2, following)

    def test_follow_in_mysql(self):
        self._test_follow()

    def test_follow_in_hbase(self):
        GateKeeper.set('switch_friendship_to_hbase', 'percent', 100)
        self._test_follow()

    def _test_follow(self):
        url = FOLLOW_URL.format(self.user1.id)
        # have to log in
        response = self.anonymous_user.post(url)
        self.assertEqual(response.status_code, 403)
        # get method not allowed
        response = self.user2_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot follow myself
        response = self.user1_client.post(url)
        self.assertEqual(response.status_code, 400)
        # user not exist
        response = self.user1_client.post(FOLLOW_URL.format(0))
        self.assertEqual(response.status_code, 404)
        # followed successfully
        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual('user' in response.data, True)
        self.assertEqual('created_at' in response.data, True)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(response.data['user']['username'], self.user1.username)
        # follow again
        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 400)
        # following adds 1 more record
        count = FriendshipService.get_following_count(self.user1.id)
        response = self.user1_client.post(FOLLOW_URL.format(self.user2.id))
        new_count = FriendshipService.get_following_count(self.user1.id)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(count + 1, new_count)

    def test_unfollow_in_mysql(self):
        self._test_unfollow()

    def test_unfollow_in_hbase(self):
        GateKeeper.set('switch_friendship_to_hbase', 'percent', 100)
        self._test_unfollow()

    def _test_unfollow(self):
        url = UNFOLLOW_URL.format(self.user1.id)
        # have to log in
        response = self.anonymous_user.post(url)
        self.assertEqual(response.status_code, 403)
        # get method not allowed
        response = self.user2_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot unfollow myself
        response = self.user1_client.post(url)
        self.assertEqual(response.status_code, 400)
        # user not exist
        response = self.user1_client.post(UNFOLLOW_URL.format(0))
        self.assertEqual(response.status_code, 404)
        # unfollow successfully
        self.create_friendship(self.user2, self.user1)
        count = FriendshipService.get_following_count(self.user2.id)
        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        new_count = FriendshipService.get_following_count(self.user2.id)
        self.assertEqual(new_count, count - 1)
        # unfollow twice (user clicks twice in very short time)
        count = FriendshipService.get_following_count(self.user2.id)
        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        new_count = FriendshipService.get_following_count(self.user2.id)
        self.assertEqual(new_count, count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.user2.id)
        # post is not allowed
        response = self.anonymous_user.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_user.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        # make sure it is ordered by 'created_at'
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(response.data['results'][0]['user']['username'], "testuser2's followings2")
        self.assertEqual(response.data['results'][1]['user']['username'], "testuser2's followings1")
        self.assertEqual(response.data['results'][2]['user']['username'], "testuser2's followings0")

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.user2.id)
        # post is not allowed
        response = self.anonymous_user.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_user.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # make sure it is ordered by 'created_at'
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(response.data['results'][0]['user']['username'], "testuser2's followers1")
        self.assertEqual(response.data['results'][1]['user']['username'], "testuser2's followers0")

    def test_followings_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            following = self.create_user('testfollowing{}'.format(i))
            Friendship.objects.create(from_user=self.user1, to_user=following)
            if following.id % 2 == 0:
                Friendship.objects.create(from_user=self.user2, to_user=following)

        url = FOLLOWINGS_URL.format(self.user1.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous does not follow anyone
        response = self.anonymous_user.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # user2 followed even id
        response = self.user2_client.get(url)
        for result in response.data['results']:
            has_followed = result['user']['id'] % 2 == 0
            self.assertEqual(result['has_followed'], has_followed)

        # user1 followed all
        response = self.user1_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

    def test_followers_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            follower = self.create_user('testfollower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.user1)
            if follower.id % 2 == 0:
                Friendship.objects.create(from_user=self.user2, to_user=follower)

        url = FOLLOWERS_URL.format(self.user1.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous does not follow anyone
        response = self.anonymous_user.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # user2 followed even id
        response = self.user2_client.get(url)
        for result in response.data['results']:
            has_followed = result['user']['id'] % 2 == 0
            self.assertEqual(result['has_followed'], has_followed)

        # user1 did not follow anyone
        response = self.user1_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

    def _test_friendship_pagination(self, url, page_size, max_page_size):
        # page 1
        response = self.anonymous_user.get(url, {'page':1, 'size': page_size})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_page'], 2)
        self.assertEqual(response.data['total_result'], 2 * page_size)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        # page 2
        response = self.anonymous_user.get(url, {'page': 2, 'size': page_size})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_page'], 2)
        self.assertEqual(response.data['total_result'], 2 * page_size)
        self.assertEqual(response.data['page_number'], 2)
        self.assertEqual(response.data['has_next_page'], False)

        # page 3
        response = self.anonymous_user.get(url, {'page': 3, 'size': page_size})
        self.assertEqual(response.status_code, 404)

        # customize page size (each page size is > max_page_size)
        response = self.anonymous_user.get(url, {'page': 1, 'size': max_page_size + 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_page'], 2)
        self.assertEqual(response.data['total_result'], 2 * page_size)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        # customize page size (each page only has 2)
        response = self.anonymous_user.get(url, {'page': 1, 'size': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['total_page'], page_size)
        self.assertEqual(response.data['total_result'], 2 * page_size)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)
