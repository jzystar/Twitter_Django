from rest_framework import serializers
from friendships.models import Friendship
from rest_framework.exceptions import ValidationError
from accounts.api.serializers import UserSerializerForFriendship
from friendships.services import FriendshipService


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

class FollowerSerializer(serializers.ModelSerializer, FollowingUserIdSetMixin):
    # 可以通过 source=xxx 指定去访问每个 model instance 的 xxx 方法
    # 即 model_instance.xxx 来获得数据
    user = UserSerializerForFriendship(source='from_user')
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    # current user checks if he followed user A's followers
    def get_has_followed(self, obj):
        return obj.from_user_id in self.following_user_id_set


class FollowingSerializer(serializers.ModelSerializer, FollowingUserIdSetMixin):
    user = UserSerializerForFriendship(source='to_user')
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    # current user checks if he followed user A's followers
    def get_has_followed(self, obj):
        return obj.to_user_id in self.following_user_id_set


class FollowingSerializerForCreate(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ['from_user_id', 'to_user_id']

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
        friendships = Friendship.objects.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id
        )

        return friendships