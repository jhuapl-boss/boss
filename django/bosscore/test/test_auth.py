# Copyright 2021 The Johns Hopkins University Applied Physics Laboratory
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

PUBLIC_COLLECTION = 'public_coll'
PUBLIC_EXPERIMENT = 'public_exp'
PUBLIC_CHANNEL = 'public_chan'
# Really, all coord frames are public.
PUBLIC_COORD_FRAME = 'public_cf'

class UserPermissionsCollection(APITestCase):
    """
    Class to test the permissions for the resource service: Collection
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        user1 = dbsetup.create_user()
        dbsetup.set_user(user1)

        self.client.force_login(user1)
        dbsetup.insert_test_data()
        dbsetup.add_collection(PUBLIC_COLLECTION, 'public-test', public=True)

        # Create a new user with different objects
        user2 = dbsetup.create_user('testuser1')
        dbsetup.add_role('resource-manager', user2)
        dbsetup.set_user(user2)
        self.client.force_login(user2)
        dbsetup.add_collection("unittestcol", "testcollection")
        

    def test_get_collection_no_permission(self):
        """
        Get a collection that the user does not have permissions on

        """
        url = '/' + version + '/collection/col1/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_collection_valid_permission(self):
        """
        Get a collection that the user has permission on

        """
        url = '/' + version + '/collection/unittestcol/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'unittestcol')

    def test_get_collection_public(self):
        """
        A public collection that the user does not have explicit permission for
        should still be readable.
        """
        url = '/' + version + f'/collection/{PUBLIC_COLLECTION}/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], PUBLIC_COLLECTION)

    def test_put_collection_no_permissions(self):
        """
        Update a collection for which the user does not have update permissions

        """
        url = '/' + version + '/collection/col1/'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_public_collection_no_permissions(self):
        """
        Update a collection for which the user does not have update permissions

        """
        url = '/' + version + f'/collection/{PUBLIC_COLLECTION}/'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_collection_valid_permission(self):
        """
        Update a collection that  the user has permissions

        """
        url = '/' + version + '/collection/unittestcol/'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_collection_name_valid_permission(self):
        """
        Update collection name  with valid permissions

        """
        url = '/' + version + '/collection/unittestcol/'
        data = {'name': 'unittestcolnew'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_collection_no_permissions(self):
        """
        Delete a collection that the user does not have permission for

        """
        url = '/' + version + '/collection/col1/'
        # Delete an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_public_collection_no_permissions(self):
        """
        Delete a collection that the user does not have permission for

        """
        url = '/' + version + f'/collection/{PUBLIC_COLLECTION}/'
        # Delete an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_collection_valid_permission(self):
        """
        Delete a collection that the user has permissions

        """
        url = '/' + version + '/collection/unittestcol1/'
        data = {'description': 'A new collection for unit tests'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_get_collections(self):
        """
        Get list of collections

        """
        url = '/' + version + '/collection/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['collections'][0], 'unittestcol')
        self.assertEqual(len(response.data['collections']), 1)


class UserPermissionsCoordinateFrame(APITestCase):
    """
    Class to test the permissions for the resource service: Coordinateframe
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        user1 = dbsetup.create_user()
        dbsetup.set_user(user1)

        self.client.force_login(user1)
        dbsetup.insert_test_data()

        # Create a new user with different objects
        user2 = dbsetup.create_user('testuser1')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(user2)
        self.client.force_login(user2)
        dbsetup.add_coordinate_frame('unittestcf', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4)

    def test_get_coordinate_frame_no_permission(self):
        """
        Get a coordinate frame that the user does not have permissions on

        """
        url = '/' + version + '/coord/cf1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_coordinate_frame_valid_permission(self):
        """
        Get a valid coordinate_frame with permissions

        """
        url = '/' + version + '/coord/unittestcf/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'unittestcf')

    def test_put_coordinate_frame_no_permissions(self):
        """
        Update a coordinate frame for which the user does not have update permissions on

        """
        url = '/' + version + '/coord/cf1'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_coordinate_frames_valid_permission(self):
        """
        Update a coordinate frames that  the user has permissions on

        """
        url = '/' + version + '/coord/unittestcf/'
        data = {'description': 'A new coordinate frame for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_coordinate_frame_name_valid_permission(self):
        """
        Update coordinate frame name (valid)

        """
        url = '/' + version + '/coord/unittestcf/'
        data = {'name': 'unittestcfnew'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_coordinate_frames_no_permissions(self):
        """
        Delete a coordinate frame that without permissions

        """
        url = '/' + version + '/coord/cf1/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_coordinate_frame_valid_permission(self):
        """
        Delete a coordinate frame that the user has permission for

        """
        url = '/' + version + '/coord/unittestcf/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_get_coordinate_frames(self):
        """
        Get list of coordinateframes

        """
        url = '/' + version + '/coord/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        #self.assertEqual(response.data['coords'][0], 'unittestcf')
        self.assertEqual(len(response.data['coords']), 2)


class UserPermissionsExperiment(APITestCase):
    """
    Class to test the resource service
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        user1 = dbsetup.create_user()
        dbsetup.set_user(user1)

        self.client.force_login(user1)
        dbsetup.insert_test_data()
        dbsetup.add_collection(PUBLIC_COLLECTION, 'public-test', public=True)
        dbsetup.add_coordinate_frame(PUBLIC_COORD_FRAME, 'Description for public cf', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4)
        dbsetup.add_experiment(PUBLIC_COLLECTION, PUBLIC_EXPERIMENT, PUBLIC_COORD_FRAME, 10, 10, 1, public=True)

        # Create a new user with different objects
        user2 = dbsetup.create_user('testuser1')
        dbsetup.set_user(user2)
        dbsetup.add_role('resource-manager')
        self.client.force_login(user2)
        dbsetup.add_collection("unittestcol", "testcollection")
        dbsetup.add_coordinate_frame('unittestcf', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4)
        dbsetup.add_experiment('unittestcol', 'unittestexp', 'unittestcf', 10, 10, 1)

    def test_get_experiment_no_permission(self):
        """
        Get a experiment that the user has no permissions for

        """
        url = '/' + version + '/collection/col1/experiment/exp1/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_experiment_valid_permission(self):
        """
        Get a valid experiment

        """
        url = '/' + version + '/collection/unittestcol/experiment/unittestexp/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'unittestexp')

    def test_get_public_experiment(self):
        """
        Get a valid experiment

        """
        url = '/' + version + f'/collection/{PUBLIC_COLLECTION}/experiment/{PUBLIC_EXPERIMENT}/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], PUBLIC_EXPERIMENT)

    def test_post_experiment_no_collection(self):
        """
        Post a new experiment (valid - No collection in the post data. This is picked up from the request)

        """

        # Get the coordinate frame id
        url = '/' + version + '/coord/unittestcf/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf = response.data['name']

        # Post a new experiment
        url = '/' + version + '/collection/unittestcol/experiment/unittestexpnew'
        data = {'description': 'This is a new experiment', 'coord_frame': cf,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'isotropic', 'num_time_samples': 10, 'dummy': 'dummy'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_experiment_no_permissions(self):
        """
        Post a new experiment (valid - No collection in the post data. This is picked up from the request)

        """

        # Get the coordinate frame id
        url = '/' + version + '/coord/unittestcf/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf = response.data['name']

        # Post a new experiment
        url = '/' + version + '/collection/col1/experiment/unittestexpnew'
        data = {'description': 'This is a new experiment', 'coord_frame': cf,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'isotropic', 'num_time_samples': 10, 'dummy': 'dummy'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_experiment_no_permissions(self):
        """
        Update an experiment for which the user does not have update permissions on

        """
        url = '/' + version + '/collection/col1/experiment/exp1/'
        data = {'description': 'A new experiment for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_public_experiment_no_permissions(self):
        """
        Update an experiment for which the user does not have update permissions on

        """
        url = '/' + version + f'/collection/{PUBLIC_COLLECTION}/experiment/{PUBLIC_EXPERIMENT}/'
        data = {'description': 'A new experiment for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_experiment_valid_permission(self):
        """
        Update a experiment that  the user has permissions on

        """
        url = '/' + version + '/collection/unittestcol/experiment/unittestexp/'
        data = {'description': 'A new experiment for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_experiment_no_permissions(self):
        """
        Delete an experiment that the user does not have permission for

        """
        url = '/' + version + '/collection/col1/experiment/exp1/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_public_experiment_no_permissions(self):
        """
        Delete an experiment that the user does not have permission for

        """
        url = '/' + version + f'/collection/{PUBLIC_COLLECTION}/experiment/{PUBLIC_EXPERIMENT}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_experiment_valid_permissions(self):
        """
        Delete an experiment that the user does have permission for

        """
        url = '/' + version + '/collection/unittestcol/experiment/unittestexp/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_get_experiments_no_permissions(self):
        """
        Get list of experiments

        """
        url = '/' + version + '/collection/col1/experiment/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['experiments'], [])

    def test_get_experiments(self):
        """
        Get list of experiments

        """
        url = '/' + version + '/collection/unittestcol/experiment/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['experiments'][0], 'unittestexp')
        self.assertEqual(len(response.data['experiments']), 1)


class UserPermissionsChannel(APITestCase):
    """
    Class to test the resource service
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        user1 = dbsetup.create_user()
        dbsetup.set_user(user1)

        self.client.force_login(user1)
        dbsetup.insert_test_data()
        dbsetup.add_collection(PUBLIC_COLLECTION, 'public-test', public=True)
        dbsetup.add_coordinate_frame(PUBLIC_COORD_FRAME, 'Description for public cf', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4)
        dbsetup.add_experiment(PUBLIC_COLLECTION, PUBLIC_EXPERIMENT, PUBLIC_COORD_FRAME, 10, 10, 1, public=True)
        dbsetup.add_channel(PUBLIC_COLLECTION, PUBLIC_EXPERIMENT, PUBLIC_CHANNEL, 0, 0, 'uint8', public=True)

        # Create a new user with different objects
        user2 = dbsetup.create_user('testuser1')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(user2)
        self.client.force_login(user2)
        dbsetup.add_collection("unittestcol", "testcollection")
        dbsetup.add_coordinate_frame('unittestcf', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4)
        dbsetup.add_experiment('unittestcol', 'unittestexp', 'unittestcf', 10, 10, 1)

        dbsetup.add_channel('unittestcol', 'unittestexp', 'unittestchannel', 0, 0, 'uint8')
        dbsetup.add_channel('unittestcol', 'unittestexp', 'unittestlayer', 0, 0, 'uint16', 'annotation', ['unittestchannel'])

    def test_get_channel_no_permission(self):
        """
        Get a channel that the user has no permissions for

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_channel_valid_permission(self):
        """
        Get a valid channel

        """
        url = '/' + version + '/collection/unittestcol/experiment/unittestexp/channel/unittestchannel'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'unittestchannel')

    def test_get_public_channel(self):
        """
        Get a public channel

        """
        url = '/' + version + f'/collection/{PUBLIC_COLLECTION}/experiment/{PUBLIC_EXPERIMENT}/channel/{PUBLIC_CHANNEL}'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], PUBLIC_CHANNEL)

    def test_post_channel(self):
        """
        Post a new channel

        """
        url = '/' + version + '/collection/unittestcol/experiment/unittestexp/channel/unittestchannelnew/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_channel_no_permissions(self):
        """
        Post a new channel .This is invalid because the user does not have add permissions for the resource
        """

        url = '/' + version + '/collection/col1/experiment/exp1/channel/unittestchannelnew/'
        data = {'description': 'This is a new channel', 'is_channel': True, 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_channel_no_permissions(self):
        """
        Update an channel for which the user does not have update permissions on

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'description': 'A new channel for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_public_channel_no_permissions(self):
        """
        Update an channel for which the user does not have update permissions on

        """
        url = '/' + version + f'/collection/{PUBLIC_COLLECTION}/experiment/{PUBLIC_EXPERIMENT}/channel/{PUBLIC_CHANNEL}'
        data = {'description': 'A new channel for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_channel_valid_permission(self):
        """
        Update a channel that  the user has permissions on

        """
        url = '/' + version + '/collection/unittestcol/experiment/unittestexp/channel/unittestchannel'
        data = {'description': 'A new channel for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_channel_no_permissions(self):
        """
        Delete an channel that the user does not have permission for

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_public_channel_no_permissions(self):
        """
        Delete an channel that the user does not have permission for

        """
        url = '/' + version + f'/collection/{PUBLIC_COLLECTION}/experiment/{PUBLIC_EXPERIMENT}/channel/{PUBLIC_CHANNEL}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_get_channels_no_permissions(self):
        """
        Get list of channels

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['channels'], [])

    def test_get_channels(self):
        """
        Get list of channels

        """
        url = '/' + version + '/collection/unittestcol/experiment/unittestexp/channel/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['channels'][0], 'unittestchannel')
