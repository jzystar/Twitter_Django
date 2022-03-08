def invalidate_following_cache(sender, instance, **kwargs):
    # there is a cycle import, so put import under function to avoid error
    from friendships.services import FriendshipService

    return FriendshipService.invalidate_following_cache(instance.from_user_id)