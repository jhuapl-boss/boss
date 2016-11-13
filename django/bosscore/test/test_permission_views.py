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

    def test_get_permission(self):
        """
        Post permissions for a valid group and collection

        """
        url = '/' + version + '/permissions/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_permission_empty(self):
        """
        Post permissions for a valid group and collection

        """
        url = '/' + version + '/permissions/?group=test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['permission-sets'], [])

    def test_post_permission_collection(self):
        """
        Post permissions for a valid group and collection

        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_invalid_permissions_collection(self):
        """
        Post  invalid  permissions strings
        """
        url = '/' + version + '/permissions/'

        data = {
            'group': 'test',
            'collection': 'col1',
            'permissions':  ['readeeee', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_permissions_invalid(self):
        """
        Post permissions to a resource or group  that does not exist

        """
        # Resource does not exist
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1eee',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

        # group does not exist
        url = '/' + version + '/permissions/'
        data = {
            'group': 'testeee',
            'collection': 'col1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_get_permission_for_collection_filter_group(self):
        """
        Get permissions for a collection
        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_permission_for_collection_filter_collection(self):
        """
        Get permissions for a collection
        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?collection=col1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_permission_for_collection_filter_collection_group(self):
        """
        Get permissions for a collection
        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test&collection=col1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_permission_invalid(self):
        """
       Get permissions for a resource that does not exist or a group that does not exist

        """
        # group does not exist
        url = '/' + version + '/permissions/?group=testeee'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # resource does not exist
        url = '/' + version + '/permissions/test/?collection=col1ee'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_permission_for_collection(self):
        """
        Delete a subset of permissions for a collection

        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test&collection=col1'

        response = self.client.delete(url, None)
        self.assertEqual(response.status_code, 204)

    def test_patch_permission_for_collection(self):
        """
        Delete a subset of permissions for a collection

        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test&collection=col1'
        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(set(resp["permission-sets"][0]["permissions"]), set(['read', 'add', 'update']))
        self.assertEqual(response.status_code, 200)

        url = '/' + version + '/permissions/test/col1'
        data = {
            'group': 'test',
            'collection': 'col1',
            'permissions': ['read']
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)

        url = '/' + version + '/permissions/?group=test&collection=col1'
        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(set(resp["permission-sets"][0]["permissions"]),set(['read']))
        self.assertEqual(response.status_code, 200)


class PermissionViewsExperimentTests(APITestCase):
    """
    Class to test the permission service which assigns permissions to experiments
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
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(self.user2)

        self.client.force_login(self.user2)
        dbsetup.create_group('test')
        dbsetup.insert_test_data()

    def test_post_permission_experiment(self):
        """
        Post permissions for a valid group and experiment

        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_invalid_permissions_experiment(self):
        """
        Post  invalid  permissions strings
        """
        url = '/' + version + '/permissions/'

        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions':  ['readeeee', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_permissions_invalid(self):
        """
        Post permissions to a resource or group  that does not exist

        """
        # Resource does not exist
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1eee',
            'experiment': 'exp1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

        # group does not exist
        url = '/' + version + '/permissions/'
        data = {
            'group': 'testeee',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_get_permission_for_collection_filter_group(self):
        """
        Get permissions for a collection
        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_permission_for_experiment_filter_experiment(self):
        """
        Get permissions for a experiment
        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?collection=col1&experiment=exp1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_permission_invalid(self):
        """
       Get permissions for a resource that does not exist or a group that does not exist

        """
        # group does not exist
        url = '/' + version + '/permissions/?group=testeee'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # resource does not exist
        url = '/' + version + '/permissions/test/?collection=col1&experiment=exp1eeeee'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_permission_for_experiment(self):
        """
        Delete a subset of permissions for a experiment

        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test&collection=col1&experiment=exp1'
        response = self.client.delete(url, None)
        self.assertEqual(response.status_code, 204)

    def test_delete_permission_for_experiment_invalid_group(self):
        """
        Delete a subset of permissions for a experiment

        """
        url = '/' + version + '/permissions/?group=testeeee&collection=col1&experiment=exp1'
        response = self.client.delete(url, None)
        self.assertEqual(response.status_code, 404)

    def test_delete_permission_for_experiment_missing_group(self):
        """
        Delete a subset of permissions for a experiment

        """
        url = '/' + version + '/permissions/?collection=col1&experiment=exp1'
        response = self.client.delete(url, None)
        self.assertEqual(response.status_code, 400)

    def test_delete_permission_for_experiment_missing_resource(self):
        """
        Delete a subset of permissions for a experiment

        """
        url = '/' + version + '/permissions/?group=test'
        response = self.client.delete(url, None)
        self.assertEqual(response.status_code, 400)

    def test_patch_permission_for_experiment(self):
        """
        Delete a subset of permissions for a experiment

        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test&collection=col1&experiment=exp1'
        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(set(resp["permission-sets"][0]["permissions"]), set(['read', 'add', 'update']))
        self.assertEqual(response.status_code, 200)

        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions': ['read']
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)

        url = '/' + version + '/permissions/?group=test&collection=col1&experiment=exp1'
        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(set(resp["permission-sets"][0]["permissions"]), set(['read']))
        self.assertEqual(response.status_code, 200)


class PermissionViewsChannelTests(APITestCase):
    """
    Class to test the permission service which assigns permissions to channels
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        self.user1 = dbsetup.create_user('testuser2555')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(self.user1)
        dbsetup.create_group('unittest2555')

        self.user2 = dbsetup.create_user('testuser')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(self.user2)

        self.client.force_login(self.user2)
        dbsetup.create_group('test')
        dbsetup.insert_test_data()

    def test_post_permission_channel(self):
        """
        Post permissions for a valid group and channel

        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_invalid_permissions_channel(self):
        """
        Post  invalid  permissions strings
        """
        url = '/' + version + '/permissions/'

        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions':  ['readeeee', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_permissions_invalid(self):
        """
        Post permissions to a resource or group  that does not exist

        """
        # Resource does not exist
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1eee',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

        # group does not exist
        url = '/' + version + '/permissions/'
        data = {
            'group': 'testeee',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_get_permission_for_channel_filter_group(self):
        """
        Get permissions for a channel
        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_permission_for_channel_filter_channel(self):
        """
        Get permissions for a channel
        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?collection=col1&experiment=exp1&channel=channel1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_permission_invalid(self):
        """
       Get permissions for a resource that does not exist or a group that does not exist

        """
        # group does not exist
        url = '/' + version + '/permissions/?group=testeee'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # resource does not exist
        url = '/' + version + '/permissions/test/?collection=col1&experiment=exp1eeeee&channel=exp1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_permission_for_channel(self):
        """
        Delete a subset of permissions for a channel

        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test&collection=col1&experiment=exp1&channel=channel1'
        response = self.client.delete(url, None)
        self.assertEqual(response.status_code, 204)

    def test_patch_permission_for_channel(self):
        """
        Delete a subset of permissions for a channel

        """
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read', 'add', 'update']
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/permissions/?group=test&collection=col1&experiment=exp1&channel=channel1'
        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(set(resp["permission-sets"][0]["permissions"]), set(['read', 'add', 'update']))
        self.assertEqual(response.status_code, 200)

        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read']
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)

        url = '/' + version + '/permissions/?group=test&collection=col1&experiment=exp1&channel=channel1'
        response = self.client.get(url)
        resp = json.loads(response.content.decode('utf-8'))
        self.assertEqual(set(resp["permission-sets"][0]["permissions"]), set(['read']))
        self.assertEqual(response.status_code, 200)

    def test_post_permissions_for_channel_not_member_maintainer(self):
        """
        Post  invalid  permissions strings
        """
        self.client.force_login(self.user1)
        url = '/' + version + '/permissions/'

        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'permissions': ['read', 'add', 'update']
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_patch_permission_for_channel_not_member_maintainer(self):
        """
        Test patch permission if user is not a member or maintainer

        """
        self.client.force_login(self.user1)
        # patch permission on a group that the user is not a member or maintainer of.
        url = '/' + version + '/permissions/'
        data = {
            'group': 'test',
            'collection': 'col1',
            'experiment': 'exp1',
            'channel': 'channel1',
            'permissions': ['read']
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_delete_permission_for_channel_not_member_maintainer(self):
        """
        Delete a subset of permissions for a channel

        """
        self.client.force_login(self.user1)
        # patch permission on a group that the user is not a member or maintainer of.
        url = '/' + version + '/permissions/?group=test&collection=col1&experiment=exp1&channel=channel1'
        response = self.client.delete(url, None)
        self.assertEqual(response.status_code, 403)
