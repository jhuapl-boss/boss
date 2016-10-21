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

import json
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
        dbsetup.add_role('resource-manager')
        dbsetup.create_group('unittest')
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_get_groups_for_current_user(self):
        """
        Test group membership for a logged in user
        Returns:

        """
        # Get all groups for the user
        url = '/' + version + '/group-member/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 2)
        self.assertEqual(response.data['groups'], ['testuser-primary', 'boss-public'])

    def test_get_groups_for_user(self):
        """
        Get groups for a specified user
        Returns:

        """
        # Get all groups for the user
        url = '/' + version + '/group-member/?username=testuser'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 2)
        self.assertEqual(response.data['groups'], ['testuser-primary', 'boss-public'])

    def test_get_members_for_group(self):
        """
        Get users for a specified group
        Returns:

        """
        # Get all groups for the user
        url = '/' + version + '/group-member/?groupname=boss-public'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['group-members']), 1)
        self.assertEqual(response.data['group-members'], ['testuser'])

    def test_get_membership_status(self):
        """
        Get membership status for a user
        Returns:

        """
        # Get all groups for the user
        url = '/' + version + '/group-member/?groupname=boss-public&username=testuser'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

        # Get all groups for the user
        url = '/' + version + '/group-member/?groupname=boss-public&username=testusereee'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_groups_for_invalid_user(self):
        """
        Get groups for a invalid user
        Returns:

        """
        # Get all groups for the user
        url = '/' + version + '/group-member/?username=testusereee'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_member_group(self):
        """ Check for usermember ship in a group. """

        # Check if user is a member of the group
        url = '/' + version + '/group-member/testuser-primary/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

        url = '/' + version + '/group-member/boss-public/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

        # Check if user is a member of the group
        url = '/' + version + '/group-member/unittest/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, False)

    def test_get_all_group_member(self):
        """ Get a list of all members in the group """

        url = '/' + version + '/group-member/?groupname=testuser-primary'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['group-members']), 1)
        self.assertEqual(response.data['group-members'][0], 'testuser')

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

        # List all members of the group
        url = '/' + version + '/group-member/?groupname=unittest'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['group-members']), 1)
        self.assertEqual(response.data['group-members'][0], 'testuser')

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
        dbsetup.add_role("resource-manager")
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
