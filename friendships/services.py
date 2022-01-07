from friendships.models import Friendship
from django.contrib.auth.models import User


class FriendshipService:

    @classmethod
    def get_followers(cls, user):
        # friendships = Friendship.objects.filter(to_user=user)
        # # .from user tigger another sql query, so n queries. Too slow
        # return [friendship.from_user for friendship in friendships]

        # select_related is doing join, too slow
        # friendships = Friendship.objects.filter(to_user=user).select_related('from_user')
        # return [friendship.from_user for friendship in friendships]

        friendships = Friendship.objects.filter(to_user=user)
        follower_ids = [friendship.from_user_id for friendship in friendships]
        followers = User.objects.filter(id__in=follower_ids)

        return followers