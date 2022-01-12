from django.db import models
from django.contrib.auth.models import User
from tweets.models import Tweet


class Comment(models.Model):
    # who comment
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # which tweet is commented
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    content = models.TextField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # order the tweet's comments by time
        index_together = (('tweet', 'created_at'), )

    def __str__(self):
        return "{} - {} says {} at tweet {}".format(
            self.created_at,
            self.user,
            self.content,
            self.tweet
        )