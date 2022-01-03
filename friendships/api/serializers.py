from rest_framework import serializers
from friendships.models import Friendship
from rest_framework.exceptions import ValidationError
from accounts.api.serializers import UserSerializerForFriendship


class FollowerSerializer(serializers.ModelSerializer):
    # 可以通过 source=xxx 指定去访问每个 model instance 的 xxx 方法
    # 即 model_instance.xxx 来获得数据
    user = UserSerializerForFriendship(source='from_user')
    class Meta:
        model = Friendship
        fields = ['user', 'created_at']


class FollowingSerializer(serializers.ModelSerializer):
    user = UserSerializerForFriendship(source='to_user')
    class Meta:
        model = Friendship
        fields = ['user', 'created_at']


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