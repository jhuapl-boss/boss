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

"""
Note that these tests all pass when run in isolation when run locally, but
there are several failures when all tests run together:

FAIL: test_delete_user (sso.tests.test_users.TestBossUser)
FAIL: test_delete_user_bossadmin (sso.tests.test_users.TestBossUser)
FAIL: test_failed_delete_user (sso.tests.test_users.TestBossUser)
FAIL: test_failed_post_user (sso.tests.test_users.TestBossUser)
FAIL: test_failed_post_user_rollback (sso.tests.test_users.TestBossUser)
FAIL: test_post_user (sso.tests.test_users.TestBossUser)
"""

from unittest import mock

# This must be imported before the views class so check_role() can be properly
# mocked.
from .test_base import TestBase, raise_error
import json

from sso.views.views_user import BossUser

from django.conf import settings
version = settings.BOSS_VERSION

class TestBossUser(TestBase):
    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_get_user(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.get_userdata.return_value = {'name':'test'}
        ctxMgr.get_realm_roles.return_value = [{'name': 'test'},{'name': 'admin'}]

        request = self.makeRequest(get='/' + version + '/sso/user/test')
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

        request = self.makeRequest(get='/' + version + '/sso/user/test')
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 500)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_post_user(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value

        data = {'first_name': 'first',
                'last_name': 'last',
                'email': 'email',
                'password': 'password'}
        request = self.makeRequest(user=self.user_mgr_user, post='/' + version + '/sso/user/test', data=data)
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data)

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

        request = self.makeRequest(user=self.user_mgr_user, post='/' + version + '/sso/user/test', data={})
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
        request = self.makeRequest(user=self.user_mgr_user, post='/' + version + '/sso/user/test', data=data)
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

        request = self.makeRequest(user=self.admin_user, delete='/' + version + '/sso/user/test')
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)

        call = mock.call.delete_user('test')
        self.assertEqual(ctxMgr.mock_calls, [call])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_delete_user_bossadmin(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value

        request = self.makeRequest(user=self.admin_user, delete='/' + version + '/sso/user/bossadmin')
        response = BossUser.as_view()(request, 'bossadmin')

        self.assertEqual(response.status_code, 500)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_delete_user(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.delete_user.side_effect = raise_error

        request = self.makeRequest(user=self.admin_user, delete='/' + version + '/sso/user/test')
        response = BossUser.as_view()(request, 'test')

        self.assertEqual(response.status_code, 500)
