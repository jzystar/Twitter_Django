from comments.models import Comment
from django.utils import timezone
from rest_framework.test import APIClient
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


class CommentApiTests(TestCase):
    
    def setUp(self):
        self.clear_cache()
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

    def test_comments_count(self):
        # create tweet and comment
        tweet = self.create_tweet(self.user1)
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.user1_client.get(url)
        # no comments
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 0)

        # test tweet list api
        self.create_comment(self.user1, tweet)
        response = self.user1_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['comments_count'], 1)

        # test newsfeeds list api
        self.create_comment(self.user2, tweet)
        self.create_newsfeed(self.user1, tweet)
        response = self.user1_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['comments_count'], 2)

    def test_comments_count_with_cache_in_redis(self):
        tweet_url = '/api/tweets/{}/'.format(self.tweet.id)
        response = self.user1_client.get(tweet_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 0)

        # add a comment
        data = {'tweet_id': self.tweet.id, 'content': 'helloworld'}
        self.user1_client.post(COMMENT_URL, data)
        response = self.user1_client.get(tweet_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 1)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 1)

        # add another comment
        comment = self.user2_client.post(COMMENT_URL, data).data
        response = self.user1_client.get(tweet_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 2)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 2)

        # update comment shouldn't update comments_count
        comment_url = '{}{}/'.format(COMMENT_URL, comment['id'])
        response = self.user2_client.put(comment_url, {'content': 'updated'})
        self.assertEqual(response.status_code, 200)
        response = self.user1_client.get(tweet_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 2)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 2)

        # delete a comment will update comments_count (only user2 can delete)
        self.user2_client.delete(comment_url)
        response = self.user1_client.get(tweet_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 1)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 1)