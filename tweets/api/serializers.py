from rest_framework import serializers
from tweets.models import Tweet
from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer
from likes.services import LikeService
from likes.api.serializers import LikeSerializer
from tweets.constants import TWEET_PHOTO_UPLOAD_LIMIT
from rest_framework.exceptions import ValidationError
from tweets.services import TweetService


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet() # adding to show user info
    # SerializerMethodField: customized method
    has_liked = serializers.SerializerMethodField() # liked or not
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments_count',
            'likes_count',
            'has_liked',
            'photo_urls',
        )

    def get_has_liked(self, obj): # liked by current user?
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_likes_count(self, obj):
        return obj.like_set.count()

    def get_comments_count(self, obj):
        return obj.comment_set.count()

    def get_photo_urls(self, obj):
        photo_urls = []
        for photo in obj.tweetphoto_set.all().order_by('order'):
            photo_urls.append(photo.file.url)

        return photo_urls


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=True, # can have empty []
        required=False, # files is not required
    )

    class Meta:
        model = Tweet
        fields = ('content', 'files')

    def validate(self, data): # check if number of files is in the limit
        if len(data.get('files', [])) > TWEET_PHOTO_UPLOAD_LIMIT:
            raise ValidationError({
                'message': f'You can only upload {TWEET_PHOTO_UPLOAD_LIMIT} photos '
                           'at most.'
            })

        return data


    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        if 'files' in validated_data:
            TweetService.create_photos_from_files(
                tweet,
                validated_data['files']
            )

        return tweet


class TweetSerializerForDetail(TweetSerializer):
    # comment.tweet => tweet.comment_set.all() 反查机制
    comments = CommentSerializer(source="comment_set", many=True)
    likes = LikeSerializer(source="like_set", many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'comments',
            'created_at',
            'content',
            'likes',
            'comments',
            'comments_count',
            'likes_count',
            'has_liked',
            'photo_urls',
        )