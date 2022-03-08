from accounts.api.serializers import UserSerializerForComment
from comments.models import Comment
from likes.services import LikeService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from tweets.models import Tweet


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerForComment(source='cached_user')
    has_liked = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'tweet_id',
            'user',
            'content',
            'created_at',
            'updated_at',
            'likes_count',
            'has_liked',
        )

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_likes_count(self, obj):
        return obj.like_set.count()


class CommentSerializerForCreate(serializers.ModelSerializer):
    tweet_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ('content', 'tweet_id')

    def validate(self, data):
        tweet_id = data['tweet_id']
        if not Tweet.objects.filter(id = tweet_id).exists():
            raise ValidationError({
                'message': 'tweet does not exist.'
            })

        return data

    def create(self, validated_data):
        user_id = self.context['request'].user.id
        tweet_id = validated_data['tweet_id']
        content = validated_data['content']
        comment = Comment.objects.create(
            user_id=user_id,
            tweet_id=tweet_id,
            content=content
        )

        return comment


class CommentSerializerForUpdate(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ('content', )

    def update(self, instance, validated_data):
        instance.content = validated_data['content']
        instance.save()

        return instance