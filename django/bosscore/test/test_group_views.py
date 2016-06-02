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
from django.conf import settings
from .setup_db import SetupTestDB

version = settings.BOSS_VERSION


class GroupMemberTests(APITestCase):
    """
    Class to test the manage-data service
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        user = dbsetup.create_user('testuser')
        dbsetup.create_group('unittest')
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_add_member_group(self):
        """ Add a new member to a group. """

        # Check if user is a member of the group
        url = '/' + version + '/group-member/unittest/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, False)

        # Add user to the group
        url = '/' + version + '/group-member/unittest/testuser/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

        # Check if user is a member of the group
        url = '/' + version + '/group-member/unittest/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

    def test_remove_member_group(self):
        """ Remove a member from the group. """

        # Add user to the group
        url = '/' + version + '/group-member/unittest/testuser/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

        # Check if user is a member of the group
        url = '/' + version + '/group-member/unittest/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

        # Remove user from the group
        url = '/' + version + '/group-member/unittest/testuser/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Check if user is a member of the group
        url = '/' + version + '/group-member/unittest/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, False)

    def test_group_member_invalid_group(self):
        """ Test group-memeber api calls with a group that does not exist """

        # Get with invalid groups
        url = '/' + version + '/group-member/unittesteee/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Post with invalid groups
        url = '/' + version + '/group-member/unittesteee/testuser/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

        # delete with invalid groups
        url = '/' + version + '/group-member/unittesteee/testuser/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_group_member_invalid_user(self):
        """ Test group-memeber api calls with a user that does not exist """

        # Get with invalid user
        url = '/' + version + '/group-member/unittest/testusereee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Post with invalid user
        url = '/' + version + '/group-member/unittest/testusereee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # delete with invalid user
        url = '/' + version + '/group-member/unittesteee/testuser/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

class GroupTests(APITestCase):
    """
    Class to test the manage-data service
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        user = dbsetup.create_user('testuser')
        dbsetup.create_group('unittest')
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_post_group(self):
        """ Add a new member to a group. """

        # Create a new group
        url = '/' + version + '/group/unittestnew/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

        # get a group
        url = '/' + version + '/group/unittestnew/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

    def test_delete_group(self):
        """ Add a new member to a group. """

        # Create a new group
        url = '/' + version + '/group/unittestnew/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

        # get a group
        url = '/' + version + '/group/unittestnew/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

        # delete
        url = '/' + version + '/group/unittestnew/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # get a group
        url = '/' + version + '/group/unittestnew/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, False)


