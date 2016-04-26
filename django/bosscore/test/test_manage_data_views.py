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
from .setup_db import SetupTestDB
from django.conf import settings

version = settings.BOSS_VERSION


class ManageDataViewsCollectionTests(APITestCase):
    """
    Class to test the manage-data service
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        user = dbsetup.create_super_user()
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_get_collection_doesnotexist(self):
        """
        Get a collection that does not exist

        """
        url = '/' + version + '/manage-data/col10/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_collection_exist(self):
        """
        Get a valid collection

        """
        url = '/' + version + '/manage-data/col1/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'col1')

    def test_post_collection(self):
        """
        Post a new collection (valid)

        """
        url = '/' + version + '/manage-data/col55/'
        data = {'description': 'A new collection for unit tests'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_collection_already_exists(self):
        """
        Post a new collection (invalid - Name already exists)

        """
        url = '/' + version + '/manage-data/col1/'
        data = {'description': 'A new collection for unit tests'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 409)

    def test_put_collection_exists(self):
        """
        Update a collection (Valid - The collection exists)

        """
        url = '/' + version + '/manage-data/col1/'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_collection_doesnotexist(self):
        """
        Update a collection that does not exist

        """
        url = '/' + version + '/manage-data/col55/'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_put_collection_name(self):
        """
        Update collection name (valid)

        """
        url = '/' + version + '/manage-data/col1/'
        data = {'name': 'col10'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_collection(self):
        """
        Delete a collection (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/manage-data/col55/'
        data = {'description': 'A new collection for unit tests'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_delete_collection_invalid(self):
        """
        Delete a collection (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/manage-data/col1/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_collection_doesnotexist(self):
        """
        Delete a collection (invalid - The collection does not exist )

        """
        url = '/' + version + '/manage-data/col10/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_get_collections(self):
        """
        Get list of collections

        """
        url = '/' + version + '/manage-data/collections/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], 'col1')


class ManageDataViewsExperimentTests(APITestCase):
    """
    Class to test the manage-data service
    """

    def setUp(self):
        """
        Initialize the database

        """

        dbsetup = SetupTestDB()
        user = dbsetup.create_super_user()
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_get_experiment_doesnotexist(self):
        """
        Get a collection that does not exist

        """
        url = '/' + version + '/manage-data/col1/exp10/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_experiment_exist(self):
        """
        Get a valid experiment

        """
        url = '/' + version + '/manage-data/col1/exp1/'

        # Get an existing experiment
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'exp1')

    def test_post_experiment(self):
        """
        Post a new experiment (valid _ the post has all the required data and does not already exist)

        """
        # Get the collection id
        url = '/' + version + '/manage-data/col1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        collection_id = response.data['id']

        # Get the coordinate frame id
        url = '/' + version + '/manage-data/coordinateframes/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf_id = response.data['id']

        # Post a new experiment
        url = '/' + version + '/manage-data/col1/exp2'
        data = {'description': 'This is a new experiment', 'collection': collection_id, 'coord_frame': cf_id,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'max_time_sample': 10}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_experiment_no_collection(self):
        """
        Post a new experiment (valid - No collection in the post data. This is picked up from the request)

        """

        # Get the coordinate frame id
        url = '/' + version + '/manage-data/coordinateframes/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf_id = response.data['id']

        # Post a new experiment
        url = '/' + version + '/manage-data/col1/exp2'
        data = {'description': 'This is a new experiment', 'coord_frame': cf_id,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'max_time_sample': 10}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_experiment_exists(self):
        """
        Post a new collection (invalid - Collection,experiment already exist)

        """

        # Get the collection id
        url = '/' + version + '/manage-data/col1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        collection_id = response.data['id']

        # Get the coordinate frame id
        url = '/' + version + '/manage-data/coordinateframes/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf_id = response.data['id']

        # Post a new experiment
        url = '/' + version + '/manage-data/col1/exp1'
        data = {'description': 'This is a new experiment', 'collection': collection_id, 'coord_frame': cf_id,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'max_time_sample': 10}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 409)

    def test_put_experiment_exists(self):
        """
        Update a experiment (Valid - The experiment exists)

        """
        url = '/' + version + '/manage-data/col1/exp1'
        data = {'description': 'A new experiment for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_experiment_doesnotexist(self):
        """
        Update a experiment that does not exist

        """
        url = '/' + version + '/manage-data/col1/exp55'
        data = {'description': 'A new experiment for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_put_experiment_name(self):
        """
        Update experiment name (valid)

        """
        url = '/' + version + '/manage-data/col1/exp1'
        data = {'name': 'exp10'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_experiment(self):
        """
        Delete a experiment

        """
        # Post a new experiment
        # Get the coordinate frame id
        url = '/' + version + '/manage-data/coordinateframes/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf_id = response.data['id']

        # Post a new experiment
        url = '/' + version + '/manage-data/col1/exp2'
        data = {'description': 'This is a new experiment', 'coord_frame': cf_id,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'max_time_sample': 10}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/manage-data/col1/exp2'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_delete_experiment_invalid(self):
        """
        Delete a experiment (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/manage-data/col1/exp1/'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_experiment_doesnotexist(self):
        """
        Delete a experiment (invalid - The experiment does not exist )

        """
        url = '/' + version + '/manage-data/col1/exp10'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_get_experiments(self):
        """
        Get list of experiments for a collection

        """
        url = '/' + version + '/manage-data/col1/experiments'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], 'exp1')


class ManageDataViewsCoordinateTests(APITestCase):
    """
    Class to test the manage-data service for coordinate frame objects
    """

    def setUp(self):
        """
        Initialize the database

        """

        dbsetup = SetupTestDB()
        user = dbsetup.create_super_user()
        dbsetup.set_user(user)
        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_get_coordinateframes(self):

        """
        Get list of coordinateframes

        """
        url = '/' + version + '/manage-data/coordinateframes/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], 'cf1')

    def test_get_coordinateframe_doesnotexist(self):
        """
        Get a coordinate frame that does not exist

        """
        url = '/' + version + '/manage-data/coordinateframes/cf10'

        # Get an coordinate frame that does not exist
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_coordinateframe_exist(self):
        """
        Get a valid coordinate frame

        """
        url = '/' + version + '/manage-data/coordinateframes/cf1'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'cf1')

    def test_post_coordinateframe(self):
        """
        Post a new coordinate frame (valid)

        """
        url = '/' + version + '/manage-data/coordinateframes/cf10'
        data = {'description': 'This is a test coordinateframe', 'x_start': 0, 'x_stop': 1000,
                'y_start': 0, 'y_stop': 1000, 'z_start': 0, 'z_stop': 1000,
                'x_voxel_size': 4, 'y_voxel_size': 4, 'z_voxel_size': 4, 'voxel_unit': 'nanometers',
                'time_step_unit': 'nanoseconds', 'time_step': 1}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_coordinateframe_already_exists(self):
        """
        Post a new coordinate frame (invalid - Name already exists)

        """
        url = '/' + version + '/manage-data/coordinateframes/cf1'
        data = {'description': 'This is a test coordinateframe', 'x_start': 0, 'x_stop': 1000,
                'y_start': 0, 'y_stop': 1000, 'z_start': 0, 'z_stop': 1000,
                'x_voxel_size': 4, 'y_voxel_size': 4, 'z_voxel_size': 4, 'voxel_unit': 'nanometers',
                'time_step_unit': 'nanoseconds', 'time_step': 1}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 409)

    def test_put_coorddinateframe_exists(self):
        """
        Update a coordinateframe (Valid - The coordinateframe exists)

        """
        url = '/' + version + '/manage-data/coordinateframes/cf1'
        data = {'description': 'This is a test coordinateframe. Updated'}

        # Update an existing coordinate frame
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_coordinateframe_doesnotexist(self):
        """
        Update a coordinateframe that does not exist

        """
        url = '/' + version + '/manage-data/coordinateframes/cf55'
        data = {'description': 'This is a test coordinateframe. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_put_coordinateframe_name(self):
        """
        Update collection name (valid)

        """
        url = '/' + version + '/manage-data/coordinateframes/cf1'
        data = {'name': 'cf10'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_coordinateframe(self):
        """
        Delete a coordinateframe (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/manage-data/coordinateframes/cf55/'
        data = {'description': 'This is a test coordinateframe', 'x_start': 0, 'x_stop': 1000,
                'y_start': 0, 'y_stop': 1000, 'z_start': 0, 'z_stop': 1000,
                'x_voxel_size': 4, 'y_voxel_size': 4, 'z_voxel_size': 4, 'voxel_unit': 'nanometers',
                'time_step_unit': 'nanoseconds', 'time_step': 1}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_delete_coordinateframe_invalid(self):
        """
        Delete a collection (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/manage-data/coordinateframes/cf1/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_coordinateframe_doesnotexist(self):
        """
        Delete a collection (invalid - The collection does not exist )

        """
        url = '/' + version + '/manage-data/coordinateframes/cf55/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)


class ManageDataViewsChannelTests(APITestCase):
    """
    Class to test the manage-data service
    """

    def setUp(self):
        """
        Initialize the database

        """

        dbsetup = SetupTestDB()
        user = dbsetup.create_super_user()
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_get_channel_doesnotexist(self):
        """
        Get a Channel that does not exist

        """
        url = '/' + version + '/manage-data/col1/exp1/channel55'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_channel_exist(self):
        """
        Get a valid experiment

        """
        url = '/' + version + '/manage-data/col1/exp1/channel1/'

        # Get an existing experiment
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'channel1')

    def test_post_channel(self):
        """
        Post a new channel (valid _ the post has all the required data and does not already exist)

        """
        # Get the experiment id
        url = '/' + version + '/manage-data/col1/exp1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        experiment_id = response.data['id']

        # Post a new channel
        url = '/' + version + '/manage-data/col1/exp1/channel10/'
        data = {'description': 'This is a new channel', 'experiment': experiment_id,
                'is_channel': True, 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_channel_layer_no_experiment(self):
        """
        Post a new channel (valid - No experiment in the post data. This is picked up from the request)

        """

        # Post a new channel

        url = '/' + version + '/manage-data/col1/exp1/channel10/'
        data = {'description': 'This is a new channel', 'is_channel': True, 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_channel_exists(self):
        """
        Post a new channel (invalid - Collection,experiment, channel already exist)

        """
        # Get the experiment id
        url = '/' + version + '/manage-data/col1/exp1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        experiment_id = response.data['id']

        # Post a new channel
        url = '/' + version + '/manage-data/col1/exp1/channel1/'
        data = {'description': 'This is a new channel', 'experiment': experiment_id,
                'is_channel': True, 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 409)

    def test_put_channel(self):
        """
        Update a channel or layer (Valid - The channel exists)

        """
        url = '/' + version + '/manage-data/col1/exp1/channel1'
        data = {'description': 'A new channel for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_channel_doesnotexist(self):
        """
        Update a channel that does not exist

        """
        url = '/' + version + '/manage-data/col1/exp1/channel55/'
        data = {'description': 'A new experiment for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_put_channel_name(self):
        """
        Update channel name (valid)

        """
        url = '/' + version + '/manage-data/col1/exp1/channel1/'
        data = {'name': 'channel10'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_channel(self):
        """
        Delete a experiment

        """
        # Post a new channel
        url = '/' + version + '/manage-data/col1/exp1/channel10/'
        data = {'description': 'This is a new channel', 'is_channel': True, 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/manage-data/col1/exp1/channel10'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    # TODO (manavpj1) - Set up this unit test
    # def test_delete_channel_invalid(self):
    #     """
    #     Delete a channel (invalid - Violates integrity constraint)
    #
    #     """
    #     url = '/' + version + '/manage-data/col1/exp1/channel1'
    #
    #     response = self.client.delete(url)
    #     self.assertEqual(response.status_code, 404)

    def test_delete_channel_doesnotexist(self):
        """
        Delete a channel (invalid - The channel does not exist )

        """
        url = '/' + version + '/manage-data/col1/exp1/channel10'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_get_channels(self):
        """
        Get list of collections

        """
        url = '/' + version + '/manage-data/col1/exp1/channels/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], 'channel1')


class ManageDataViewsLayerTests(APITestCase):
    """
    Class to test the manage-data service
    """

    def setUp(self):
        """
        Initialize the database

        """

        dbsetup = SetupTestDB()
        user = dbsetup.create_super_user()
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_get_layer_doesnotexist(self):
        """
        Get a Layer that does not exist

        """
        url = '/' + version + '/manage-data/col1/exp1/layer55'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_layer_exist(self):
        """
        Get a valid layer

        """
        url = '/' + version + '/manage-data/col1/exp1/layer1/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'layer1')

    def test_post_layer(self):
        """
        Post a new layer (valid _ the post has all the required data and does not already exist)

        """
        # Get the experiment id
        url = '/' + version + '/manage-data/col1/exp1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        experiment_id = response.data['id']

        # Get channelid
        url = '/' + version + '/manage-data/col1/exp1/channel1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        channel_id = response.data['id']

        # Post a new channel
        url = '/' + version + '/manage-data/col1/exp1/layer10/'
        data = {'description': 'This is a new layer', 'experiment': experiment_id,
                'is_channel': False, 'datatype': 'uint8',
                'channels': [1]}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_layer_no_experiment(self):
        """
        Post a new layer (valid - No experiment in the post data. This is picked up from the request)

        """

        # Post a new layer

        url = '/' + version + '/manage-data/col1/exp1/layer10/'
        data = {'description': 'This is a new layer', 'is_channel': False, 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_layer_exists(self):
        """
        Post a new layer (invalid - Collection,experiment, layer already exist)

        """
        # Get the experiment id
        url = '/' + version + '/manage-data/col1/exp1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        experiment_id = response.data['id']

        # Post a new layer
        url = '/' + version + '/manage-data/col1/exp1/layer1/'
        data = {'description': 'This is a new layer', 'experiment': experiment_id,
                'is_channel': True, 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 409)

    def test_put_layer(self):
        """
        Update a channel or layer (Valid - The layer exists)

        """
        url = '/' + version + '/manage-data/col1/exp1/layer1'
        data = {'description': 'A new layer for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_layer_doesnotexist(self):
        """
        Update a layer that does not exist

        """
        url = '/' + version + '/manage-data/col1/exp1/layer55/'
        data = {'description': 'A new layer for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_put_layer_name(self):
        """
        Update layer name (valid)

        """
        url = '/' + version + '/manage-data/col1/exp1/layer1/'
        data = {'name': 'layer10'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_layer(self):
        """
        Delete a layer

        """
        # Post a new layer
        url = '/' + version + '/manage-data/col1/exp1/layer10/'
        data = {'description': 'This is a new layer', 'is_channel': False, 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/manage-data/col1/exp1/layer10'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    # TODO (manavpj1) - Set up this unit test
    # def test_delete_channel_invalid(self):
    #     """
    #     Delete a channel (invalid - Violates integrity constraint)
    #
    #     """
    #     url = '/' + version + '/manage-data/col1/exp1/channel1'
    #
    #     response = self.client.delete(url)
    #     self.assertEqual(response.status_code, 404)

    def test_delete_channel_doesnotexist(self):
        """
        Delete a channel (invalid - The channel does not exist )

        """
        url = '/' + version + '/manage-data/col1/exp1/layer10'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_get_layers(self):
        """
        Get list of layers

        """
        url = '/' + version + '/manage-data/col1/exp1/layers/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], 'layer1')
