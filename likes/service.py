from likes.models import Like
from django.contrib.contenttypes.models import ContentType


class LikeService:

    @classmethod
    def has_liked(cls, user, target):
        if user.is_anonymous:
            return False

        return Like.objects.filter(
            object_id=target.id,
            content_type=ContentType.objects.get_for_model(target.__class__),
            user=user
        ).exists()