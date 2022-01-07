from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from tweets.models import Tweet
from rest_framework.test import APIClient


class TestCase(DjangoTestCase):
    
    @property
    def anonymous_user(self):
        if hasattr(self, '_anonymous_user'):
            return self._anonymous_user
        self._anonymous_user = APIClient()
        return self._anonymous_user

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = 'generic password'
        if email is None:
            email = f'{username}@twitter.com'

        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'

        return Tweet.objects.create(user=user, content=content)