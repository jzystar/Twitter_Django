from django.conf import settings
from django.core.cache import caches
from friendships.models import Friendship
from friendships.models import HBaseFollower, HBaseFollowing
from gatekeeper.models import GateKeeper
from time import time
from twitter.cache import FOLLOWINGS_PATTERN

cache = caches['testing'] if settings.TESTING else caches['default']


class FriendshipService:

    # @classmethod
    # def get_followers(cls, user):
        # friendships = Friendship.objects.filter(to_user=user)
        # # .from user tigger another sql query, so n queries. Too slow
        # return [friendship.from_user for friendship in friendships]

        # select_related is doing join, too slow
        # friendships = Friendship.objects.filter(to_user=user).select_related('from_user')
        # return [friendship.from_user for friendship in friendships]

        # correct version 1
        # friendships = Friendship.objects.filter(to_user=user)
        # follower_ids = [friendship.from_user_id for friendship in friendships]
        # followers = User.objects.filter(id__in=follower_ids)

        # correct version 2
        # friendships = Friendship.objects.filter(
        #     to_user=user,
        # ).prefetch_related('from_user')
        # followers = [friendship.from_user for friendship in friendships]
        #
        # return followers

    @classmethod
    def get_follower_ids(cls, tweet_user_id):
        friendships = Friendship.objects.filter(to_user_id=tweet_user_id)
        return [friendship.from_user_id for friendship in friendships]

    @classmethod
    def get_following_user_id_set(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        user_id_set = cache.get(key)
        if user_id_set is not None:
            return user_id_set

        friendships = Friendship.objects.filter(from_user_id=from_user_id)
        user_id_set = set([friendship.to_user_id for friendship in friendships])
        cache.set(key, user_id_set)

        return user_id_set

    # when follow a new user or unfollow, cache needs to be deleted
    @classmethod
    def invalidate_following_cache(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        cache.delete(key)
    # delete rather than update
    # ex: 3 -> {1, 2, 4}
    # follow 5 and 6 concurrent, write {1, 2, 4, 5} and write {1, 2, 4, 6},
    # suppose to have {1, 2, 4, 5, 6}

    @classmethod
    def follow(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            # crate friendship in MySQL
            return Friendship.objects.create(
                from_user_id=from_user_id,
                to_user_id=to_user_id
            )

        # create friendship in HBase
        now = int(time() * 1000000)
        HBaseFollower.create(
            created_at=now,
            to_user_id=to_user_id,
            from_user_id=from_user_id
        )
        return HBaseFollowing.create(
            from_user_id = from_user_id,
            created_at = now,
            to_user_id = to_user_id
        )

    @classmethod
    def get_follow_instance_from_hbase(cls, from_user_id, to_user_id):
        friendships = HBaseFollowing.filter(prefix=(from_user_id, ))
        for friendship in friendships:
            if friendship.to_user_id == to_user_id:
                return friendship

        return None

    @classmethod
    def has_followed(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return True

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            return Friendship.objects.filter(
                from_user_id=from_user_id,
                to_user_id=to_user_id
            ).exists()

        friendship = cls.get_follow_instance_from_hbase(from_user_id, to_user_id)
        return friendship != None

    @classmethod
    def get_following_count(cls, from_user_id):
        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            return Friendship.objects.filter(from_user_id=from_user_id).count()

        friendships = HBaseFollowing.filter(prefix=(from_user_id,))
        return len(friendships)