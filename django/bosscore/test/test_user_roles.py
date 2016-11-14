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
from django.test import TestCase
from django.conf import settings
from .setup_db import SetupTestDB
from bosscore.privileges import BossPrivilegeManager

version = settings.BOSS_VERSION


class UserPrivilegeTests(TestCase):
    """
    Class to test a users privilege
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        self.dbsetup = SetupTestDB()
        user = self.dbsetup.create_user('testuser')
        self.dbsetup.add_role('user-manager')
        self.client.force_login(user)

    def test_get_all_roles(self):

        bpm = BossPrivilegeManager('testuser')
        roles = bpm.get_user_roles()
        self.assertEqual('default' in roles, True)
        self.assertEqual('resource-manager' in roles, False)

        self.dbsetup.add_role('resource-manager')
        roles = bpm.get_user_roles()
        self.assertEqual('resource-manager' in roles, True)

    def test_has_role(self):

        bpm = BossPrivilegeManager('testuser')
        self.assertEqual(bpm.has_role('user-manager'), True)
        self.assertEqual(bpm.has_role('resource-manager'), False)
