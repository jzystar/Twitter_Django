from django.contrib.contenttypes.models import ContentType
from tweets.models import Tweet
from comments.models import Comment
from notifications.signals import notify


class NotificationService:

    @classmethod
    def send_like_notification(cls, like):
        target = like.content_object
        if like.user == target.user:
            return

        if like.content_type == ContentType.objects.get_for_model(Tweet):
            notify.send(
                like.user,
                recipient=target.user,
                verb='liked your tweet',
                target=target
            )
        if like.content_type == ContentType.objects.get_for_model(Comment):
            notify.send(
                like.user,
                recipient=target.user,
                verb='like your comment',
                target=target
            )

    @classmethod
    def send_comment_notification(cls, comment):
        target = comment.tweet
        if comment.user == target.user:
            return

        notify.send(
            comment.user,
            recipient=target.user,
            verb='comment on your tweet',
            target=target
        )