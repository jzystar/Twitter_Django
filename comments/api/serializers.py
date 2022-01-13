from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from comments.models import Comment
from tweets.models import Tweet
from accounts.api.serializers import UserSerializerForComment


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerForComment()

    class Meta:
        model = Comment
        fields = ('id', 'tweet_id', 'user', 'content', 'created_at', 'updated_at')


class CommentSerializerForCreate(serializers.ModelSerializer):
    tweet_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ('content', 'tweet_id')

    def validate(self, data):
        tweet_id = data['tweet_id']
        if not Tweet.objects.filter(id = tweet_id).exists():
            raise ValidationError({
                'message': 'tweet does not exist'
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