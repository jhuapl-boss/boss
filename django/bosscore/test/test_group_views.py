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


class GroupsTests(APITestCase):
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

    def test_get_groups(self):
        """ Get all groups for a user"""

        # get a group
        url = '/' + version + '/groups/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['groups']), set(['bosspublic', 'testuser-primary', 'unittest']))

    def test_get_groups_groupname(self):
        """ Get all groups for a user"""

        url = '/' + version + '/permissions/'
        data = {
            'group': 'unittest',
            'collection': 'col1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/'
        data = {
            'group': 'unittest',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/'
        data = {
            'group': 'unittest',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # get a group
        url = '/' + version + '/groups/unittest'
        response = self.client.get(url)
        resources = response.data['resources']
        self.assertEqual(len(resources), 3)
        self.assertEqual(response.status_code, 200)

    def test_get_groups_groupname_no_resources(self):
        """ Get all groups for a user"""
        # get a group
        url = '/' + version + '/groups/unittest'
        response = self.client.get(url)
        resources = response.data['resources']
        self.assertEqual(len(resources), 0)
        self.assertEqual(response.status_code, 200)

    def test_get_groups_filter_members(self):
        """ Get all groups for a user is a member of """

        # get a group
        url = '/' + version + '/groups/?filter=member'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['groups']), set(['bosspublic', 'testuser-primary', 'unittest']))

    def test_get_groups_filter_maintainers(self):
        """ Get all groups for a user is a member of """

        # get a group
        url = '/' + version + '/groups/?filter=maintainer'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['groups']), set(['unittest']))

    def test_post_groups(self):
        """ Post new group """

        # post a group
        url = '/' + version + '/groups/pjm55'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

        # get the group
        url = '/' + version + '/groups/?filter=maintainer'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['groups']), set(['pjm55', 'unittest']))

    def test_delete_groups(self):
        """ Post new group """

        # post a group
        url = '/' + version + '/groups/pjm55'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

        # delete a group
        url = '/' + version + '/groups/pjm55'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)


class GroupMemberTests(APITestCase):
    """
    Class to test gropup member views
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        self.user1 = dbsetup.create_user('testuser2555')
        dbsetup.set_user(self.user1)
        dbsetup.create_group('unittest2555')

        self.user2 = dbsetup.create_user('testuser')
        dbsetup.add_role("resource-manager")
        dbsetup.create_group('unittest')
        dbsetup.set_user(self.user2)

        self.client.force_login(self.user2)
        dbsetup.insert_test_data()

    def test_get_members(self):
        """ Get all members of a group"""

        # get a group
        url = '/' + version + '/groups/unittest/members'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['members']), set(['testuser']))

    def test_get_members_no_permission(self):
        """ Get all members of a group"""

        # get a group
        url = '/' + version + '/groups/unittest2555/members'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_members_username(self):
        """ Get all members of a group"""

        # List all members of the group
        url = '/' + version + '/groups/unittest/members'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['members']), 1)

        # get a group
        url = '/' + version + '/groups/unittest/members/testuser'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], True)

        # get a group
        url = '/' + version + '/groups/unittest/members/testuser2555'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], False)

    def test_add_member_group(self):
        """ Add a new member to a group. """

        # Check if user is a member of the group
        url = '/' + version + '/groups/unittest/members/testuser2555/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], False)

        # Add user to the group
        url = '/' + version + '/groups/unittest/members/testuser2555/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)

        # Check if user is a member of the group
        url = '/' + version + '/groups/unittest/members/testuser2555/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], True)

        # List all members of the group
        url = '/' + version + '/groups/unittest/members'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['members']), 2)

    def test_remove_member_group(self):
        """ Remove a member from the group. """

        # Add user to the group
        url = '/' + version + '/groups/unittest/members/testuser2555/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)

        # Check if user is a member of the group
        url = '/' + version + '/groups/unittest/members/testuser2555/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], True)

        # Remove user from the group
        url = '/' + version + '/groups/unittest/members/testuser2555/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Check if user is a member of the group
        url = '/' + version + '/groups/unittest/members/testuser2555/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], False)

    def test_group_member_invalid_group(self):
        """ Test group-memeber api calls with a group that does not exist """

        # get a group
        url = '/' + version + '/groups/eeeeee/members'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Post with invalid groups
        url = '/' + version + '/groups/eeeeee/members/testuser/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

        # delete with invalid groups
        url = '/' + version + '/groups/eeeeee/members/testuser/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_group_member_invalid_user(self):
        """ Test group member api calls with a user that does not exist """

        # Get with invalid user
        url = '/' + version + '/groups/unittest/members/testusereee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Post with invalid user
        url = '/' + version + '/groups/unittest/members/testusereee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # delete with invalid user
        url = '/' + version + '/groups/unittest/members/testusereee/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_group_member_missing_permission(self):
        """ Test group member api calls with a user that does not exist """

        # Post with invalid user
        url = '/' + version + '/groups/unittest2555/members/testuser/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        # delete with invalid user
        url = '/' + version + '/groups/unittest2555/members/testuser/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_get_members_permission(self):
        """ Test that group maintainers can query the list of members"""
        self.client.force_login(self.user1)

        # get a group
        url = '/' + version + '/groups/unittest/members'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user2)
        #
        # # Add user1 to the group maintainer
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)

        # get a group
        url = '/' + version + '/groups/unittest/members'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['members']), set(['testuser']))

    def test_get_members_permission_for_group_member(self):
        """ Test that group members can query the list of maintainers"""
        self.client.force_login(self.user1)

        # get a group
        url = '/' + version + '/groups/unittest/members'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user2)
        #
        # # Add user1 to the group
        url = '/' + version + '/groups/unittest/members/testuser2555/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)

        # get a group
        url = '/' + version + '/groups/unittest/members'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['members']), set(['testuser','testuser2555']))

class GroupMaintainerTests(APITestCase):
    """
    Class to test group maintainer views
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        self.user1 = dbsetup.create_user('testuser2555')
        dbsetup.set_user(self.user1)
        dbsetup.create_group('unittest2555')

        self.user2 = dbsetup.create_user('testuser')
        dbsetup.add_role("resource-manager")
        dbsetup.create_group('unittest')
        dbsetup.set_user(self.user2)

        self.client.force_login(self.user2)
        dbsetup.insert_test_data()

    def test_get_maintainers(self):
        """ Get all members of a group"""

        # get a group
        url = '/' + version + '/groups/unittest/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['maintainers']), set(['testuser']))

    def test_get_maintainers_no_permissions(self):
        """ Get all maintainers of a group without permissions"""

        # get a group
        url = '/' + version + '/groups/unittest2555/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_maintainers_username(self):
        """ Get all members of a group"""

        # get a group
        url = '/' + version + '/groups/unittest/maintainers/testuser'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], True)

        # get a group
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], False)

    def test_add_maintainer_invalid(self):
        """ Add a new member to a group. """

        # Add maintainer to the group
        url = '/' + version + '/groups/unittest/maintainers/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_add_maintainer_group(self):
        """ Add a new member to a group. """

        # Check if user is a maintainer of the group
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], False)

        # Add user to the group
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)

        # get a group
        url = '/' + version + '/groups/unittest/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Check if user is a member of the group
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], True)

        # List all members of the group
        url = '/' + version + '/groups/unittest/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['maintainers']), 2)

    def test_remove_maintainer_group(self):
        """ Remove a maintainer from the group. """

        # Add maintainer to the group
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)

        # Check if user is a member of the group
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], True)

        # List all members of the group
        url = '/' + version + '/groups/unittest/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Remove user from the group
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Check if user is a member of the group
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result'], False)

        # List all members of the group
        url = '/' + version + '/groups/unittest/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('testuser', response.data['maintainers'])

    def test_group_maintainer_invalid_group(self):
        """ Test group-maintainer api calls with a group that does not exist """

        # get a group
        url = '/' + version + '/groups/eeeeee/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Post with invalid groups
        url = '/' + version + '/groups/eeeeee/maintainers/testuser/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

        # delete with invalid groups
        url = '/' + version + '/groups/eeeeee/maintainers/testuser/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_group_member_invalid_user(self):
        """ Test group member api calls with a user that does not exist """

        # Get with invalid user
        url = '/' + version + '/groups/unittest/maintainers/testusereee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Post with invalid user
        url = '/' + version + '/groups/unittest/maintainers/testusereee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # delete with invalid user
        url = '/' + version + '/groups/unittest/maintainers/testusereee/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_group_member_missing_permission(self):
        """ Test group member api calls with a user that does not exist """

        # Post with invalid user
        url = '/' + version + '/groups/unittest2555/maintainers/testuser/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        # delete with invalid user
        url = '/' + version + '/groups/unittest2555/maintainers/testuser/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_get_maintainers_permission(self):
        """ Test that group maintainers can query the list of maintainers"""
        self.client.force_login(self.user1)

        # get a group
        url = '/' + version + '/groups/unittest/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user2)
        #
        # # Add user1 to the group maintainer
        url = '/' + version + '/groups/unittest/maintainers/testuser2555/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)

        # get a group
        url = '/' + version + '/groups/unittest/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['maintainers']), set(['testuser','testuser2555']))

    def test_get_maintainers_permission_for_group_member(self):
        """ Test that group members can query the list of maintainers"""
        self.client.force_login(self.user1)

        # get a group
        url = '/' + version + '/groups/unittest/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user2)
        #
        # # Add user1 to the group maintainer
        url = '/' + version + '/groups/unittest/members/testuser2555/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)

        # get a group
        url = '/' + version + '/groups/unittest/maintainers'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['maintainers']), set(['testuser']))

