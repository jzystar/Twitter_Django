from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_delete
from friendships.listeners import invalidate_following_cache
from utils.memcached_helper import MemcachedHelper


class Friendship(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="following_friendship_set"
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="follower_friendship_set"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            # get people I am following, order by crated_at
            ('from_user', 'created_at'),
            # get people who are following me, order by created_at
            ('to_user', 'created_at'),
        )
        unique_together = (('from_user', 'to_user'), )

    def __str__(self):
        return '{} followed {}'.format(self.from_user, self.to_user)

    @property
    def cached_from_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.from_user_id)

    @property
    def cached_to_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.to_user_id)

# delete will trigger pre_delete
pre_delete.connect(invalidate_following_cache, sender=Friendship)
# create and update will trigger post_save
post_save.connect(invalidate_following_cache, sender=Friendship)