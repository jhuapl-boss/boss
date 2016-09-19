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

from rest_framework.test import APITestCase
from django.core.urlresolvers import resolve

from django.conf import settings

from bosscore.views.views_user import BossUserRole, BossUser

version = settings.BOSS_VERSION


class BossCoreUserRoutingTests(APITestCase):

    def test_user_resolves(self):
        """
        Test that all group urls resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/sso/user/test-user/')
        self.assertEqual(match.func.__name__, BossUser.as_view().__name__)


    def test_user_role_resolves(self):
        """
        Test that all group_member urls for experiments resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/sso/user-role/test/user-manager/')
        self.assertEqual(match.func.__name__, BossUserRole.as_view().__name__)

        match = resolve('/' + version + '/sso/user-role/test/')
        self.assertEqual(match.func.__name__, BossUserRole.as_view().__name__)




