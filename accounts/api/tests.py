from testing.testcases import TestCase
from rest_framework.test import APIClient
from accounts.models import UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile


LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'
USER_PROFILE_DETAIL_URL = '/api/profiles/{}/'


class AccountApiTests(TestCase):

    def setUp(self):
        # 这个函数会在每个 test function 执行的时候被执行
        self.clear_cache()
        self.client = APIClient()
        self.user = self.create_user(
            username='admin',
            email='admin@jiuzhang.com',
            password='correct password',
        )

    def test_login(self):
        # must begin with test_, otherwise it won't be called automatically
        # must use post method, but used get
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        # log in failed，http status code 405 = METHOD_NOT_ALLOWED
        self.assertEquals(response.status_code, 405)

        # change to post, but use wrong password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password'
        })
        self.assertEqual(response.status_code, 400)

        # check if not logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEquals(response.data['has_logged_in'], False)

        # use correct password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'admin@jiuzhang.com')

        # check if logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # log in first
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })
        # check if logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEquals(response.data['has_logged_in'], True)

        # must use post, but use get
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # change to post, logout successfully
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)
        # check if logged out
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@gmail.com',
            'password': 'any password'
        }
        # must use post method, but used get
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # use wrong email
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not correct email',
            'password': 'any password'
        })
        self.assertEquals(response.status_code, 400)

        # too short password
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@gmail.com',
            'password': '123'
        })
        self.assertEquals(response.status_code, 400)

        # too long username
        response = self.client.post(SIGNUP_URL, {
            'username': 'username is tooooooooooooooooo loooooooong',
            'email': 'someone@gmail.com',
            'password': 'any password'
        })
        self.assertEquals(response.status_code, 400)

        # sign up successfully
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')

        # check if logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # check user profile exists
        user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=user_id).first()
        self.assertNotEqual(profile, None)


class UserProfileAPITests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_avatar_update(self):
        user1_profile = self.user1.profile
        user1_profile.nickname = 'old nickname'
        user1_profile.save()
        url = USER_PROFILE_DETAIL_URL.format(user1_profile.id)

        # anonymous user cannot update
        response = self.anonymous_user.put(url, {'nickname': 'new nickname'})
        self.assertEqual(response.status_code, 403)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

        # only owner can update
        response = self.user2_client.put(url, {'nickname': 'new nickname'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'You do not have the permission to access this object')
        user1_profile.refresh_from_db()
        self.assertEqual(user1_profile.nickname, 'old nickname')

        # owner update successfully
        response = self.user1_client.put(url, {'nickname': 'new nickname'})
        self.assertEqual(response.status_code, 200)
        user1_profile.refresh_from_db()
        self.assertEqual(user1_profile.nickname, 'new nickname')

        # update avatar
        response = self.user1_client.put(url, {
            'avatar': SimpleUploadedFile(
                name='my-avatar.jpeg',
                content=str.encode('a test image'),
                content_type='image/jpeg'
            )
        })
        user1_profile.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual('my-avatar' in response.data['avatar'], True)
        self.assertNotEqual(user1_profile.avatar, None)