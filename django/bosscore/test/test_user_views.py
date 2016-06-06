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


class UserRoleTests(APITestCase):
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
        dbsetup.set_user(user)

        self.client.force_login(user)

    def test_get_user_role(self):
        """ Add a new member to a group. """

        # Check if user has the role
        url = '/' + version + '/user-role/testuser/user-manager/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, False)

        # Check if user has the role
        url = '/' + version + '/user-role/testuser/resource-manager/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

    def test_get_user_role_list(self):
        """ Add a new member to a group. """

        # Check if user has the role
        url = '/' + version + '/user-role/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        print (response.data)


    def test_add_user_role(self):
        """ Add a new member to a group. """

        # Check if user has the role
        url = '/' + version + '/user-role/testuser/user-manager/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, False)

        # Assign role to the user
        url = '/' + version + '/user-role/testuser/user-manager/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        # Check if user has the role
        url = '/' + version + '/user-role/testuser/user-manager/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

    def test_remove_user_role(self):
        """ Remove a role from a user. """

        # Assign role to the user
        url = '/' + version + '/user-role/testuser/user-manager/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        # Check if user has the role
        url = '/' + version + '/user-role/testuser/user-manager/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

        # Remove role from the user
        url = '/' + version + '/user-role/testuser/user-manager/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Check if user has the role
        url = '/' + version + '/user-role/testuser/user-manager/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, False)

    def test_user_role_invalid_user(self):
        """ Test user-role api calls with a user that does not exist """

        # Get with invalid user
        url = '/' + version + '/user-role/testusereeee/user-manager/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Post with invalid user
        url = '/' + version + '/user-role/testusereeee/user-manager/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

        # delete with invalid user
        url = '/' + version + '/user-role/testusereeee/user-manager/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_user_role_invalid_role(self):
        """ Test user-role api calls with a role that does not exist """

        # Get with invalid user
        url = '/' + version + '/user-role/testuser/user-managereee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Post with invalid user
        url = '/' + version + '/user-role/testuser/user-managereee/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

        # delete with invalid user
        url = '/' + version + '/user-role/testuser/user-managereee/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)


class UserTests(APITestCase):
    """
    Class to test the API for managing Boss Users
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

    def test_get_user(self):
        """ Get a user """

        # Get the user
        url = '/' + version + '/user/testuser/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_user(self):
        """Add a new user """

        # Create a new user
        url = '/' + version + '/user/eee/'
        data = {'first_name': 'Test', 'last_name': 'name', 'email': 'test@theboss.io', 'password': 'testpassword'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_user_exists(self):
        """Add a new user """

        # Create a new user
        url = '/' + version + '/user/testuser/'
        # data = {'first_name': 'Test', 'last_name': 'name', 'email': 'test@theboss.io', 'password': 'testpassword'}
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_user(self):
        """ Add a user. """

        # Create a new user
        url = '/' + version + '/user/eee/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

        #Get the user
        url = '/' + version + '/user/eee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Delete the user
        url = '/' + version + '/user/eee/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)

        # Get the user
        url = '/' + version + '/user/eee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def create_new_user_complete(self):

        # Create a new user
        url = '/' + version + '/user/eee/'
        data = {'first_name': 'Test', 'last_name': 'name', 'email': 'test@theboss.io', 'password': 'testpassword'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Check if the user's primary group got created
        url = '/' + version + '/group/eee-primary/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Check if user is a member of the the primary group
        url = '/' + version + '/group-member/eee-primary/eee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)

        # Check if user is a member of the public group
        url = '/' + version + '/group-member/boss-public/eee/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, True)


class UserGroupsTests(APITestCase):
    """
    Class to test the API for Listing a users group
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

    def test_get_user_groups(self):
        """ Get a user """

        # Get the user
        url = '/' + version + '/user/testuser/groups'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(resp), 2)
        self.assertEqual(resp[0]['name'], 'testuser-primary')

        # Add user to the group
        url = '/' + version + '/group-member/unittest/testuser/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/user/testuser/groups'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(resp), 3)
        print (resp)


