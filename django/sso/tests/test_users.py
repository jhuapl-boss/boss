# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from unittest import mock
import sys, json

class KeyCloakError(Exception):
    def __init__(self, status, data):
        super(KeyCloakError, self).__init__(data)
        self.status = status
        self.data = data

def raise_error(*args, **kwargs):
    raise KeyCloakError(500, {})

sys.modules['bossutils'] = mock.Mock()
sys.modules['bossutils.aws'] = mock.Mock()
sys.modules['bossutils.logger'] = mock.Mock()
sys.modules['bossutils.keycloak'] = mock.Mock()
mock.patch('bosscore.privileges.check_role', lambda x: lambda y: y).start() # apply right now
from sso.views.views_user import BossUser
import sso.views.views_user
sso.views.views_user.KeyCloakError = KeyCloakError

from django.test import TestCase
from django.conf import settings

VERSION = settings.BOSS_VERSION
TEST_USER = 'testuser'

class TestBossUser(APITestCase):
    def setUp(self):
        """
        Initialize the database
        :return:
        """
        self.user = User.objects.create_user(username=TEST_USER)

    def makeRequest(self, get=None, post=None, delete=None, data=None):
        factory = APIRequestFactory()

        if get is not None:
            request = factory.get(get)
        elif post is not None:
            request = factory.post(post, data)
        elif delete is not None:
            request = factory.delete(delete)
        else:
            raise Exception('Unsupported request type')

        force_authenticate(request, user=self.user)

        return request

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_get_user(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.get_userdata.return_value = {'name':'test'}
        ctxMgr.get_realm_roles.return_value = [{'name': 'test'},{'name': 'admin'}]

        request = self.makeRequest(get='/v0.6/sso/user/test')
        response = BossUser.as_view()(request, 'test') # arguments are not parsed out

        self.assertEqual(response.status_code, 200)

        # Role 'test' will be filtered out by the view
        data = {'name':'test', 'realmRoles':['admin']}
        self.assertEqual(response.data, data)

        call1 = mock.call.get_userdata('test')
        call2 = mock.call.get_realm_roles('test')
        self.assertEqual(ctxMgr.mock_calls, [call1, call2])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_get_user(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.get_userdata.side_effect = raise_error

        request = self.makeRequest(get='/v0.6/sso/user/test')
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 500)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_post_user(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value

        data = {'first_name': 'first',
                'last_name': 'last',
                'email': 'email',
                'password': 'password'}
        request = self.makeRequest(post='/v0.6/sso/user/test', data=data)
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 201)

        call1 = mock.call.create_user(json.dumps({'username': 'test',
                                                  'firstName': 'first',
                                                  'lastName': 'last',
                                                  'email': 'email',
                                                  'enabled': True}))
        call2 = mock.call.reset_password('test', {'type': 'password',
                                                  'temporary': False,
                                                  'value': 'password'})
        self.assertEqual(ctxMgr.mock_calls, [call1, call2])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_post_user(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.create_user.side_effect = raise_error

        request = self.makeRequest(post='/v0.6/sso/user/test', data={})
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 500)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_post_user_rollback(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.reset_password.side_effect = raise_error

        data = {'first_name': 'first',
                'last_name': 'last',
                'email': 'email',
                'password': 'password'}
        request = self.makeRequest(post='/v0.6/sso/user/test', data=data)
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 500)

        call1 = mock.call.create_user(json.dumps({'username': 'test',
                                                  'firstName': 'first',
                                                  'lastName': 'last',
                                                  'email': 'email',
                                                  'enabled': True}))
        call2 = mock.call.reset_password('test', {'type': 'password',
                                                  'temporary': False,
                                                  'value': 'password'})
        call3 = mock.call.delete_user('test') # make sure the user is deleted
        self.assertEqual(ctxMgr.mock_calls, [call1, call2, call3])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_delete_user(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value

        request = self.makeRequest(delete='/v0.6/sso/user/test')
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 204)

        call = mock.call.delete_user('test')
        self.assertEqual(ctxMgr.mock_calls, [call])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_delete_user(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.delete_user.side_effect = raise_error

        request = self.makeRequest(delete='/v0.6/sso/user/test')
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 500)
