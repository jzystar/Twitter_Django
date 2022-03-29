from accounts.api.serializers import UserSerializerForFriendship
from accounts.services import UserService
from friendships.models import Friendship
from friendships.services import FriendshipService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class FollowingUserIdSetMixin:

    @property
    def following_user_id_set(self):
        # not logged in user
        if self.context['request'].user.is_anonymous:
            return set([])

        if hasattr(self, '_cached_following_user_id_set'):
            return self._cached_following_user_id_set
        user_id_set = FriendshipService.get_following_user_id_set(
            self.context['request'].user.id
        )
        setattr(self, '_cached_following_user_id_set', user_id_set)

        return user_id_set


class FollowerSerializer(serializers.Serializer, FollowingUserIdSetMixin):
    user = serializers.SerializerMethodField()
    has_followed = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_user(self, obj):
        user = UserService.get_user_through_cache(obj.from_user_id)
        # .data is required due to SerializerMethodField
        return UserSerializerForFriendship(user).data

    # current user checks if he followed user A's followers
    def get_has_followed(self, obj):
        return obj.from_user_id in self.following_user_id_set

    def get_created_at(self, obj):
        return obj.created_at


class FollowingSerializer(serializers.Serializer, FollowingUserIdSetMixin):
    user = serializers.SerializerMethodField()
    has_followed = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_user(self, obj):
        user = UserService.get_user_through_cache(obj.to_user_id)
        return UserSerializerForFriendship(user).data

    # current user checks if he followed user A's followers
    def get_has_followed(self, obj):
        return obj.to_user_id in self.following_user_id_set

    def get_created_at(self, obj):
        return obj.created_at


class FollowingSerializerForCreate(serializers.Serializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    def validate(self, attrs):
        if attrs['from_user_id'] == attrs['to_user_id']:
            raise ValidationError({
                'message': 'You cannot follow yourself.'
            })
        if Friendship.objects.filter(
                from_user_id=attrs['from_user_id'],
                to_user_id=attrs['to_user_id']
        ).exists():
            raise ValidationError({
                'message': 'You have already followed this user.'
            })

        return attrs

    def create(self, validate_data):
        from_user_id = validate_data['from_user_id']
        to_user_id = validate_data['to_user_id']
        friendships = FriendshipService.follow(from_user_id, to_user_id)

        return friendships