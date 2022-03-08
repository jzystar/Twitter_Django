from testing.testcases import TestCase
from rest_framework.test import APIClient
from tweets.models import Tweet, TweetPhoto
from django.core.files.uploadedfile import SimpleUploadedFile
from utils.paginations import EndlessPagination


TWEET_LIST_API = '/api/tweets/' # must end with /
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'


class TweetApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('user1', 'user1@gmail.com')
        # create 3 tweets
        self.tweets1 = [self.create_tweet(self.user1) for _ in range(3)]
        self.user1_client = APIClient()
        # forcibly authenticate a request
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2', 'user2@gmail.com')
        self.tweets2 = [self.create_tweet(self.user2) for _ in range(2)]
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_list_api(self):
        # no user_id
        response = self.anonymous_user.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        # correct request for user1
        response = self.anonymous_user.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)

        # correct request for user2
        response = self.anonymous_user.get(TWEET_LIST_API, {'user_id': self.user2.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # check the order
        self.assertEqual(response.data['results'][0]['id'], self.tweets2[1].id)
        self.assertEqual(response.data['results'][1]['id'], self.tweets2[0].id)

    def test_create_api(self):
        # not logged in
        response = self.anonymous_user.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 403)

        # no content
        response = self.user1_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 400)
        # short content
        response = self.user1_client.post(TWEET_CREATE_API, {'content': '1'})
        self.assertEqual(response.status_code, 400)
        # long content
        response = self.user1_client.post(TWEET_CREATE_API, {'content': '1'*141})
        self.assertEqual(response.status_code, 400)

        # correct post
        tweets_count = Tweet.objects.count()
        response = self.user1_client.post(TWEET_CREATE_API, {'content': 'Hello world!'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Tweet.objects.count(), tweets_count + 1)
    
    def test_retrieve(self):
        # wrong tweet id 
        url = TWEET_RETRIEVE_API.format(0)
        response = self.anonymous_user.get(url)
        self.assertEqual(response.status_code, 404)
        
        # get all comments
        tweet = self.create_tweet(self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)
        response = self.anonymous_user.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # add comments
        self.create_comment(self.user1, tweet)
        self.create_comment(self.user2, tweet)
        another_tweet = self.create_tweet(self.user2)
        self.create_comment(self.user1, another_tweet)
        response = self.anonymous_user.get(url)
        self.assertEqual(len(response.data['comments']), 2)

    def test_create_with_files(self):
        # upload empty files
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'test content',
            'files': []
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        # upload one picture
        file = SimpleUploadedFile(
            name='test.jpeg',
            content=str.encode('a test image'),
            content_type='image/jpeg'
        )
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'test content',
            'files': [file]
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 1)

        # upload multiple pictures
        file1 = SimpleUploadedFile(
            name='test1.jpeg',
            content=str.encode('a test1 image'),
            content_type='image/jpeg'
        )
        file2 = SimpleUploadedFile(
            name='test2.jpeg',
            content=str.encode('a test2 image'),
            content_type='image/jpeg'
        )
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'test content again',
            'files': [file1, file2]
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 3)

        # test tweet retrieve, should have photos too
        url = TWEET_RETRIEVE_API.format(response.data['id'])
        response = self.user1_client.get(url)
        self.assertEqual(len(response.data['photo_urls']), 2)
        self.assertEqual('test1' in response.data['photo_urls'][0], True)
        self.assertEqual('test2' in response.data['photo_urls'][1], True)

        # upload more than the limit
        files = [
            SimpleUploadedFile(
                name='picture{}.jpeg'.format(i),
                content=str.encode('a test picture{} image'.format(i)),
                content_type='image/jpeg'
            ) for i in range(10)
        ]
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'test content over limit pictures',
            'files': files
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(TweetPhoto.objects.count(), 3)

    def test_endless_pagination(self):
        page_size = EndlessPagination.page_size
        # setup has created a few tweets, minus the length in order to have page_size * 2
        for i in range(page_size * 2 - len(self.tweets1)):
            self.tweets1.append(self.create_tweet(self.user1, 'tweet'.format(i)))
        tweets = self.tweets1[::-1]

        # pull the 1st page
        response = self.user1_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[0].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[page_size - 1].id)
        
        # pull the 2nd page
        response = self.user1_client.get(TWEET_LIST_API,{
            'user_id': self.user1.id,
            'created_at__lt': tweets[page_size - 1].created_at
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[page_size + 1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[2 * page_size - 1].id)
        
        # pull the latest tweets
        response = self.user1_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id,
            'created_at__gt': tweets[0].created_at
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)
        # crate a new tweet
        new_tweet = self.create_tweet(self.user1)
        response = self.user1_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id,
            'created_at__gt': tweets[0].created_at
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_tweet.id)
        