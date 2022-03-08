from friendships.models import Friendship
from friendships.services import  FriendshipService
from testing.testcases import TestCase


class FriendshipServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('testuser1')
        self.user2 = self.create_user('testuser2')
        self.user3 = self.create_user('testuser3')

    def test_get_followings(self):
        user4 = self.create_user('testuser4')
        for to_user in [self.user1, self.user2, self.user3]:
            Friendship.objects.create(from_user=user4, to_user=to_user)
        # FriendshipService.invalidate_following_cache(user4.id)

        user_id_set = FriendshipService.get_following_user_id_set(user4.id)
        self.assertEqual(user_id_set, set([self.user1.id, self.user2.id, self.user3.id]))

        # delete user
        Friendship.objects.filter(from_user=user4, to_user=self.user1).delete()
        # FriendshipService.invalidate_following_cache(user4.id)
        user_id_set = FriendshipService.get_following_user_id_set(user4.id)
        self.assertEqual(user_id_set, set([self.user2.id, self.user3.id]))

        # follow a new user
        user5 = self.create_user('testuser5')
        Friendship.objects.create(from_user=user4, to_user=user5)
        # FriendshipService.invalidate_following_cache(user4.id)
        user_id_set = FriendshipService.get_following_user_id_set(user4.id)
        self.assertEqual(user_id_set, set([self.user2.id, self.user3.id, user5.id]))

