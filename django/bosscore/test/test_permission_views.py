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
import json

version = settings.BOSS_VERSION


class PermissionViewsCollectionTests(APITestCase):
    """
    Class to test the permission service which assigns permissions to collections
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
        dbsetup.create_group('test')
        dbsetup.insert_test_data()

    def test_post_permission_collection(self):
        """
        Post permissions for a valid group and collection

        """
        url = '/' + version + '/permission/test/col1'
        data = {'permissions': ['read', 'add', 'update']}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_invalid_permissions_collection(self):
        """
        Post  invalid  permissions strings
        """
        url = '/' + version + '/permission/test/col1'
        data = {'permissions': ['readeeee', 'add', 'update']}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_post_permissions_invalid(self):
        """
        Post permissions to a resource or group  that does not exist

        """
        # Resource does not exist
        url = '/' + version + '/permission/test/col1eee'
        data = {'permissions': ['read', 'add', 'update']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

        # group does not exist
        url = '/' + version + '/permission/testee/col1'
        data = {'permissions': ['read', 'add', 'update']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_get_permission_for_collection(self):
        """
        Get permissions for a collection
        """
        url = '/' + version + '/permission/test/col1'
        data = {'permissions': ['read', 'add', 'update']}
        self.client.post(url, data=data)

        url = '/' + version + '/permission/test/col1'

        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resp['permissions']), 3)

    def test_get_permission_invalid(self):
        """
       Get permissions for a resource that does not exist or a group that does not exist

        """
        # group does not exist
        url = '/' + version + '/permission/testee/col1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # resource does not exist
        url = '/' + version + '/permission/test/col1ee'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_permission_for_collection(self):
        """
        Delete a subset of permissions for a collection

        """
        url = '/' + version + '/permission/test/col1'
        data = {'permissions': ['read', 'add', 'update']}
        self.client.post(url, data=data)

        url = '/' + version + '/permission/test/col1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permission/test/col1'
        data = {'permissions': ['update']}
        response = self.client.delete(url, data=data)
        self.assertEqual(response.status_code, 200)

        url = '/' + version + '/permission/test/col1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 201)


class PermissionViewsExperimentTests(APITestCase):
    """
    Class to test the permission service which assigns permissions to experiments
    """

    def setUp(self):
        """
        Initialize the database

        """
        dbsetup = SetupTestDB()
        user = dbsetup.create_user('testuser')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.create_group('test')
        dbsetup.insert_test_data()

    def test_post_permission_experiment(self):
        """
        Post new permissions for a experiment

        """
        url = '/' + version + '/permission/test/col1/exp1'
        data = {'permissions': ['read']}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_invalid_permissions_experiment(self):
        """
        Post  invalid  permissions strings
        """
        url = '/' + version + '/permission/test/col1/exp1'
        data = {'permissions': ['readeeee', 'add', 'update']}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_post_permissions_invalid_experiment(self):
        """
        Post permissions to a resource or group  that does not exist

        """
        # Resource does not exist
        url = '/' + version + '/permission/test/col1/exp1ee'
        data = {'permissions': ['read', 'add', 'update']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

        # group does not exist
        url = '/' + version + '/permission/testee/col1/exp1'
        data = {'permissions': ['read', 'add', 'update']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_get_permission_for_experiment(self):
        """
        Get permissions for a experiment
        """
        url = '/' + version + '/permission/test/col1/exp1'
        data = {'permissions': ['read', 'add', 'update']}
        self.client.post(url, data=data)

        url = '/' + version + '/permission/test/col1/exp1'

        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resp['permissions']), 3)

    def test_delete_permission_for_experiment(self):
        """
        Delete permission for a experiment

        """
        # Post some permissions
        url = '/' + version + '/permission/test/col1/exp1'
        data = {'permissions': ['read', 'add', 'update']}
        self.client.post(url, data=data)

        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resp['permissions']), 3)

        # delete a subset of permissions
        data = {'permissions': ['update']}
        response = self.client.delete(url, data=data)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resp['permissions']), 2)

        # delete all permissions
        data = {'permissions': ['read', 'update', 'add']}
        response = self.client.delete(url, data=data)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resp['permissions']), 0)


class PermissionViewsChannelTests(APITestCase):
    """
    Class to test the permission service which assigns permissions to Channel
    """

    def setUp(self):
        """
        Initialize the database

        """
        dbsetup = SetupTestDB()
        user = dbsetup.create_user('testuser')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.create_group('test')
        dbsetup.insert_test_data()

    def test_post_permission_channel(self):
        """
        Post a new collection (valid)

        """
        url = '/' + version + '/permission/test/col1/exp1/channel1/'
        data = {'permissions': ['read']}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_invalid_permissions_channel(self):
        """
        Post  invalid  permissions
        """
        url = '/' + version + '/permission/test/col1/exp1/channel1'
        data = {'permissions': ['readeeee', 'add', 'update']}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_post_permissions_invalid_channel(self):
        """
        Post permissions to a resource or group  that does not exist

        """
        # Resource does not exist
        url = '/' + version + '/permission/test/col1/exp1/cheeeee'
        data = {'permissions': ['read', 'add', 'update']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

        # group does not exist
        url = '/' + version + '/permission/testee/col1/exp1/channel1'
        data = {'permissions': ['read', 'add', 'update']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_get_permission_for_channel(self):
        """
        Post a new collection (valid)

        """
        url = '/' + version + '/permission/test/col1/exp1/channel1'
        data = {'permissions': ['read', 'add', 'update']}
        self.client.post(url, data=data)

        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resp['permissions']), 3)

    def test_delete_permission_for_channel(self):
        """
        Delete permission for a channel

        """
        # Post some permissions
        url = '/' + version + '/permission/test/col1/exp1/channel1'
        data = {'permissions': ['read', 'add', 'update']}
        self.client.post(url, data=data)

        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resp['permissions']), 3)

        # delete a subset of permissions
        data = {'permissions': ['update']}
        response = self.client.delete(url, data=data)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resp['permissions']), 2)

        # delete all permissions
        data = {'permissions': ['read', 'update', 'add']}
        response = self.client.delete(url, data=data)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resp['permissions']), 0)
