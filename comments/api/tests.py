from testing.testcases import TestCase
from rest_framework.test import APIClient
from comments.models import Comment
from django.utils import timezone


COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'


class CommentApiTests(TestCase):
    
    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)
        self.tweet = self.create_tweet(self.user1)
        
        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)
        
    def test_create(self):
        # have to log in
        response = self.anonymous_user.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)
        
        # no parameter
        response = self.user1_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)
        
        # only have tweet_id
        response = self.user1_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        # only have content
        response = self.user1_client.post(COMMENT_URL, {'content': 'Hello'})
        self.assertEqual(response.status_code, 400)

        # content too long
        response = self.user1_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1'*141
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)

        # comment successfully
        response = self.user1_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id, 'content': '1'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')

    def test_destroy(self):
        comment = self.create_comment(self.user1, self.tweet)
        url = COMMENT_DETAIL_URL.format(comment.id)

        # have to log in
        response = self.anonymous_user.delete(url)
        self.assertEqual(response.status_code, 403)

        # only owner can delete
        response = self.user2_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # owner can delete
        count = Comment.objects.count()
        response = self.user1_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update(self):
        comment = self.create_comment(self.user1, self.tweet)
        url = COMMENT_DETAIL_URL.format(comment.id)
        another_tweet = self.create_tweet(self.user2)

        # have to log in
        response = self.anonymous_user.put(url)
        self.assertEqual(response.status_code, 403)

        # only owner can update
        response = self.user2_client.put(url)
        self.assertEqual(response.status_code, 403)

        # only able to update content
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.user1_client.put(url, {
            'content': 'new',
            'user_id': self.user2.id,
            'tweet_id': another_tweet.id,
            'created_at': now
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db() # update computer memory
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.user1)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_list(self):
        # must have tweet_id
        response = self.anonymous_user.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # with tweet_id
        response = self.anonymous_user.get(COMMENT_URL, {
            'tweet_id': self.tweet.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # comments order by time
        self.create_comment(self.user1, self.tweet, '1')
        self.create_comment(self.user2, self.tweet, '2')
        self.another_tweet = self.create_tweet(self.user2)
        self.create_comment(self.user2, self.another_tweet, '3')
        response = self.anonymous_user.get(COMMENT_URL, {
            'tweet_id': self.tweet.id
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        # provide both of user_id and tweet_id, only tweet_id works
        response = self.anonymous_user.get(COMMENT_URL,{
            'tweet_id': self.tweet.id,
            'user_id': self.user1.id
        })
        self.assertEqual(len(response.data['comments']), 2)