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

FAIL: test_delete_role (sso.tests.test_user_roles.TestBossUserRole)
FAIL: test_failed_delete_role (sso.tests.test_user_roles.TestBossUserRole)
FAIL: test_failed_get_role (sso.tests.test_user_roles.TestBossUserRole)
FAIL: test_failed_post_role (sso.tests.test_user_roles.TestBossUserRole)
FAIL: test_get_role_no_role (sso.tests.test_user_roles.TestBossUserRole)
FAIL: test_get_role_with_role (sso.tests.test_user_roles.TestBossUserRole)
FAIL: test_get_role_with_role1 (sso.tests.test_user_roles.TestBossUserRole)
FAIL: test_post_role (sso.tests.test_user_roles.TestBossUserRole)
"""

from unittest import mock
import json

from .test_base import TestBase, raise_error, TEST_USER, ADMIN_USER

from sso.views.views_user import BossUserRole

from django.conf import settings
version = settings.BOSS_VERSION

class TestBossUserRole(TestBase):
    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_get_role_no_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.get_realm_roles.return_value = [{'name': 'test'},{'name': 'admin'}]

        request = self.makeRequest(user=self.user_mgr_user, get='/' + version + '/sso/user-role/testuser')
        response = BossUserRole.as_view()(request, 'testuser')

        self.assertEqual(response.status_code, 200)

        # Role 'test' will be filtered out by the view
        self.assertEqual(response.data, ['admin'])

        call = mock.call.get_realm_roles('testuser')
        self.assertEqual(ctxMgr.mock_calls, [call])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_get_role_with_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.get_realm_roles.return_value = [{'name': 'test'},{'name': 'admin'}]

        request = self.makeRequest(user=self.user_mgr_user, get='/' + version + '/sso/user-role/testuser/admin')
        response = BossUserRole.as_view()(request, 'testuser', 'admin')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data, True)

        call = mock.call.get_realm_roles('testuser')
        self.assertEqual(ctxMgr.mock_calls, [call])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_get_role_with_role_as_kwarg(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.get_realm_roles.return_value = [{'name': 'test'},{'name': 'admin'}]

        request = self.makeRequest(user=self.user_mgr_user, get='/' + version + '/sso/user-role/testuser/admin')
        response = BossUserRole.as_view()(request, 'testuser', role_name='admin')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data, True)

        call = mock.call.get_realm_roles('testuser')
        self.assertEqual(ctxMgr.mock_calls, [call])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_get_role_as_admin(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.get_realm_roles.return_value = [{'name': 'test'}]

        request = self.makeRequest(user=self.admin_user, get='/' + version + '/sso/user-role/testuser/admin')
        response = BossUserRole.as_view()(request, 'testuser', role_name='admin')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data, False)

        call = mock.call.get_realm_roles('testuser')
        self.assertEqual(ctxMgr.mock_calls, [call])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_get_role_bad_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.get_realm_roles.return_value = [{'name': 'test'},{'name': 'admin'}]

        request = self.makeRequest(get='/' + version + '/sso/user-role/testuser/test')
        response = BossUserRole.as_view()(request, 'testuser', 'test')

        self.assertEqual(response.status_code, 403)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_get_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.get_realm_roles.side_effect = raise_error

        request = self.makeRequest(user=self.user_mgr_user, get='/' + version + '/sso/user-role/testuser')
        response = BossUserRole.as_view()(request, 'testuser')

        self.assertEqual(response.status_code, 500)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_get_self_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value

        request = self.makeRequest(user=self.user, get='/' + version + '/sso/user-role')
        response = BossUserRole.as_view()(request)

        self.assertEqual(response.status_code, 200)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_post_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value

        request = self.makeRequest(user=self.user_mgr_user, post='/' + version + '/sso/user-role/testuser/resource-manager')
        response = BossUserRole.as_view()(request, 'testuser', 'resource-manager')

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data)

        call = mock.call.map_role_to_user('testuser', 'resource-manager')
        self.assertEqual(ctxMgr.mock_calls, [call])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_post_admin_role(self, mKCC):
        """The admin roles is not allowed to be assigned through the API"""
        ctxMgr = mKCC.return_value.__enter__.return_value

        request = self.makeRequest(post='/' + version + '/sso/user-role/testuser/admin')
        response = BossUserRole.as_view()(request, 'testuser', 'admin')

        self.assertEqual(response.status_code, 403)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_post_role_bad_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value

        request = self.makeRequest(user=self.user, post='/' + version + '/sso/user-role/testuser/test')
        response = BossUserRole.as_view()(request, 'testuser', 'test')

        self.assertEqual(response.status_code, 403)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_post_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.map_role_to_user.side_effect = raise_error

        request = self.makeRequest(user=self.user_mgr_user, post='/' + version + '/sso/user-role/testuser/resource-manager')
        response = BossUserRole.as_view()(request, 'testuser', 'resource-manager')

        self.assertEqual(response.status_code, 500)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_delete_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value

        request = self.makeRequest(user=self.user_mgr_user, delete='/' + version + '/sso/user-role/testuser/resource-manager')
        response = BossUserRole.as_view()(request, 'testuser', 'resource-manager')

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)

        call = mock.call.remove_role_from_user('testuser', 'resource-manager')
        self.assertEqual(ctxMgr.mock_calls, [call])

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_delete_role_bad_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value

        request = self.makeRequest(user=self.user, delete='/' + version + '/sso/user-role/testuser/test')
        response = BossUserRole.as_view()(request, 'testuser', 'test')

        self.assertEqual(response.status_code, 403)

    @mock.patch('sso.views.views_user.KeyCloakClient', autospec = True)
    def test_failed_delete_role(self, mKCC):
        ctxMgr = mKCC.return_value.__enter__.return_value
        ctxMgr.remove_role_from_user.side_effect = raise_error

        request = self.makeRequest(user=self.admin_user, delete='/' + version + f'/sso/user-role/foo/resource-manager')
        response = BossUserRole.as_view()(request, 'foo', 'resource-manager')

        self.assertEqual(response.status_code, 500)
