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


class ResourceViewsCollectionTests(APITestCase):
    """
    Class to test the resource service
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
        dbsetup.insert_test_data()

    def test_get_collection_doesnotexist(self):
        """
        Get a collection that does not exist

        """
        url = '/' + version + '/collection/col10/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_collection_exist(self):
        """
        Get a valid collection

        """
        url = '/' + version + '/collection/col1/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'col1')

    def test_post_collection(self):
        """
        Post a new collection (valid)

        """
        url = '/' + version + '/collection/col55'
        data = {'description': 'A new collection for unit tests'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_collection_special_characters(self):
        """
        Post a new collection (valid)

        """
        url = '/' + version + '/collection/col55-22'
        data = {'description': 'A new collection for unit tests'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'col55-22')

    def test_post_collection_already_exists(self):
        """
        Post a new collection (invalid - Name already exists)

        """
        url = '/' + version + '/collection/col1/'
        data = {'description': 'A new collection for unit tests'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_collection_no_data(self):
        """
        Post a new collection (valid)

        """
        url = '/' + version + '/collection/col55/'
        # Get an existing collection
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

    def test_put_collection_exists(self):
        """
        Update a collection (Valid - The collection exists)

        """
        url = '/' + version + '/collection/col1/'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_collection_doesnotexist(self):
        """
        Update a collection that does not exist

        """
        url = '/' + version + '/collection/col55/'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_put_collection_name(self):
        """
        Update collection name (valid)

        """
        url = '/' + version + '/collection/col1/'
        data = {'name': 'col10'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_collection(self):
        """
        Delete a collection (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/collection/col55/'
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
        url = '/' + version + '/collection/col1/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_collection_doesnotexist(self):
        """
        Delete a collection (invalid - The collection does not exist )

        """
        url = '/' + version + '/collection/col10/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_get_collections(self):
        """
        Get list of collections

        """
        url = '/' + version + '/collection/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['collections'][0], 'col1')


class ResourceViewsExperimentTests(APITestCase):
    """
    Class to test the resource service
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
        dbsetup.insert_test_data()

    def test_get_experiment_doesnotexist(self):
        """
        Get a collection that does not exist

        """
        url = '/' + version + '/collection/col1/experiment/exp10/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_experiment_exist(self):
        """
        Get a valid experiment

        """
        url = '/' + version + '/collection/col1/experiment/exp1/'

        # Get an existing experiment
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'exp1')

    def test_post_experiment(self):
        """
        Post a new experiment (valid _ the post has all the required data and does not already exist)

        """
        # Get the coordinate frame id
        url = '/' + version + '/coord/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf = response.data['name']

        # Post a new experiment
        url = '/' + version + '/collection/col1/experiment/exp2'
        data = {'description': 'This is a new experiment', 'coord_frame': cf,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'num_time_samples': 10}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_experiment_not_unique(self):
        """
        Post a new experiment with a name that already exists in the database but is unique to the collection

        """
        # Get the coordinate frame id
        url = '/' + version + '/coord/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf = response.data['name']

        # Post a new experiment
        url = '/' + version + '/collection/col2/experiment/exp1'
        data = {'description': 'This is a new experiment', 'coord_frame': cf,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'num_time_samples': 10}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_experiment_no_collection(self):
        """
        Post a new experiment (valid - No collection in the post data. This is picked up from the request)

        """

        # Get the coordinate frame id
        url = '/' + version + '/coord/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf = response.data['name']

        # Post a new experiment
        url = '/' + version + '/collection/col1/experiment/exp2'
        data = {'description': 'This is a new experiment', 'coord_frame': cf,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'num_time_samples': 10, 'dummy': 'dummy'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_experiment_no_time(self):
        """
        Post a new experiment (valid - No time in post data)

        """

        # Get the coordinate frame id
        url = '/' + version + '/coord/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf = response.data['name']

        # Post a new experiment
        url = '/' + version + '/collection/col1/experiment/exp2'
        data = {'description': 'This is a new experiment', 'coord_frame': cf,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp2/'
        # Get an existing experiment
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'exp2')
        self.assertEqual(response.data['num_time_samples'], 1)

    def test_post_experiment_exists(self):
        """
        Post a new collection (invalid - Collection,experiment already exist)

        """

        # Get the collection id
        url = '/' + version + '/collection/col1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Get the coordinate frame id
        url = '/' + version + '/coord/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf = response.data['name']

        # Post a new experiment
        url = '/' + version + '/collection/col1/experiment/exp1'
        data = {'description': 'This is a new experiment', 'coord_frame': cf,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'num_time_samples': 10}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_experiment_no_data(self):
        """
        Post a new experiment (invalid _ the post has no body)

        """
        # Post a new experiment
        url = '/' + version + '/collection/col1/experiment/exp2'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_put_experiment_exists(self):
        """
        Update a experiment (Valid - The experiment exists)

        """
        url = '/' + version + '/collection/col1/experiment/exp1'
        data = {'description': 'A new experiment for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_experiment_doesnotexist(self):
        """
        Update a experiment that does not exist

        """
        url = '/' + version + '/collection/col1/experiment/exp55'
        data = {'description': 'A new experiment for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_put_experiment_name(self):
        """
        Update experiment name (valid)

        """
        url = '/' + version + '/collection/col1/experiment/exp1'
        data = {'name': 'exp10'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_experiment(self):
        """
        Delete a experiment

        """
        # Post a new experiment
        # Get the coordinate frame id
        url = '/' + version + '/coord/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf = response.data['name']

        # Post a new experiment
        url = '/' + version + '/collection/col1/experiment/exp2'
        data = {'description': 'This is a new experiment', 'coord_frame': cf,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'num_time_samples': 10}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp2'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_delete_experiment_invalid(self):
        """
        Delete a experiment (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/collection/col1/experiment/exp1/'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_experiment_doesnotexist(self):
        """
        Delete a experiment (invalid - The experiment does not exist )

        """
        url = '/' + version + '/collection/col1/experiment/exp10'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_get_experiments(self):
        """
        Get list of experiments for a collection

        """
        url = '/' + version + '/collection/col1/experiment/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['experiments'][0], 'exp1')


class ResourceViewsCoordinateTests(APITestCase):
    """
    Class to test the resource service for coordinate frame objects
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
        dbsetup.insert_test_data()

    def test_get_coordinateframes(self):

        """
        Get list of coordinateframes

        """
        url = '/' + version + '/coord/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['coords'][0], 'cf1')

    def test_get_coordinateframe_doesnotexist(self):
        """
        Get a coordinate frame that does not exist

        """
        url = '/' + version + '/coord/cf10'

        # Get an coordinate frame that does not exist
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_coordinateframe_exist(self):
        """
        Get a valid coordinate frame

        """
        url = '/' + version + '/coord/cf1'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'cf1')

    def test_post_coordinateframe(self):
        """
        Post a new coordinate frame (valid)

        """
        url = '/' + version + '/coord/cf10'
        data = {'description': 'This is a test coordinateframe', 'x_start': 0, 'x_stop': 1000,
                'y_start': 0, 'y_stop': 1000, 'z_start': 0, 'z_stop': 1000,
                'x_voxel_size': 4, 'y_voxel_size': 4, 'z_voxel_size': 4, 'voxel_unit': 'nanometers',
                'time_step_unit': 'nanoseconds', 'time_step': 1}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_coordinateframe_no_time_step(self):
        """
        Post a new coordinate frame without a time_step. This is set ot None (valid)

        """
        url = '/' + version + '/coord/cf10'
        data = {'description': 'This is a test coordinateframe', 'x_start': 0, 'x_stop': 1000,
                'y_start': 0, 'y_stop': 1000, 'z_start': 0, 'z_stop': 1000,
                'x_voxel_size': 4, 'y_voxel_size': 4, 'z_voxel_size': 4, 'voxel_unit': 'nanometers'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/coord/cf10'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'cf10')
        self.assertEqual(response.data['time_step'], None)
        self.assertEqual(response.data['time_step_unit'], None)

    def test_post_coordinateframe_already_exists(self):
        """
        Post a new coordinate frame (invalid - Name already exists)

        """
        url = '/' + version + '/coord/cf1'
        data = {'description': 'This is a test coordinateframe', 'x_start': 0, 'x_stop': 1000,
                'y_start': 0, 'y_stop': 1000, 'z_start': 0, 'z_stop': 1000,
                'x_voxel_size': 4, 'y_voxel_size': 4, 'z_voxel_size': 4, 'voxel_unit': 'nanometers',
                'time_step_unit': 'nanoseconds', 'time_step': 1}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_put_coorddinateframe_exists(self):
        """
        Update a coordinateframe (Valid - The coordinateframe exists)

        """
        url = '/' + version + '/coord/cf1'
        data = {'description': 'This is a test coordinateframe. Updated'}

        # Update an existing coordinate frame
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_coorddinateframe_extrafields(self):
        """
        Update a coordinateframe (Valid - The coordinateframe exists)

        """
        url = '/' + version + '/coord/cf1'
        data = {'description': 'This is a test coordinateframe. Updated', 'x_start': 22}

        # Update an existing coordinate frame
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_put_coordinateframe_doesnotexist(self):
        """
        Update a coordinateframe that does not exist

        """
        url = '/' + version + '/coord/cf55'
        data = {'description': 'This is a test coordinateframe. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_put_coordinateframe_name(self):
        """
        Update collection name (valid)

        """
        url = '/' + version + '/coord/cf1'
        data = {'name': 'cf10'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_coordinateframe(self):
        """
        Delete a coordinateframe (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/coord/cf55/'
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
        url = '/' + version + '/coord/cf1/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_coordinateframe_doesnotexist(self):
        """
        Delete a collection (invalid - The collection does not exist )

        """
        url = '/' + version + '/coord/cf55/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)


class ResourceViewsChannelTests(APITestCase):
    """
    Class to test the resource service
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
        dbsetup.insert_test_data()

    def test_get_channel_doesnotexist(self):
        """
        Get a Channel that does not exist

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel55'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_channel_exist(self):
        """
        Get a valid experiment

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1/'

        # Get an existing experiment
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'channel1')

    def test_post_channel(self):
        """
        Post a new channel (Valid - the post has all the required data and does not already exist)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_channel_with_valid_timestep(self):
        """
        Post a new channel with the default_time_step

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image', 'default_time_sample': 5}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_channel_with_invalid_timestep(self):
        """
        Post a new channel with the default_time_step

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image', 'default_time_sample': 15}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_channel_with_valid_base_resolution(self):
        """
        Post a new channel with the base_resolution

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image', 'base_resolution': 5}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_channel_with_invalid_base_resolution(self):
        """
        Post a new channel with the an invalid base_resolution

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image', 'base_resolution': 15}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_channel_no_experiment(self):
        """
        Post a new channel (valid - No experiment in the post data. This is picked up from the request)

        """

        # Post a new channel

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'type': 'image', 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_channel_exists(self):
        """
        Post a new channel (invalid - Collection,experiment, channel already exist)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1/'
        data = {'description': 'This is a new channel', 'type': 'image', 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_channel_annotation_without_source(self):
        """
        Post a new channel of type annotation(invalid - source missing)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_channel_annotation_with_source(self):
        """
        Post a new channel of type annotation

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'sources': ['channel1'], 'related': ['channel2']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Get an existing experiment
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['sources'], ['channel1'])
        self.assertEqual(response.data['related'], ['channel2'])

    def test_post_channel_annotation_with_multiple_sources(self):
        """
        Post a new channel of type annotation(invalid - source missing)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'sources': ['channel1', 'channel2']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Get an existing experiment
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['sources'], ['channel1', 'channel2'])

        # Ensure that this is Asymmetrical
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['sources'], [])

    def test_post_channel_annotation_with_common_source_related(self):
        """
        Post a new channel of type annotation(invalid - source missing)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'sources': ['channel1'],
                'related': ['channel1', 'channel3']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_channel_bad_source(self):
        """
        Post a new channel of type annotation(invalid - source missing)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'sources': ['channel1eeee'],
                'related': ['channel1', 'channel3']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_channel_bad_related(self):
        """
        Post a new channel of type annotation(invalid - source missing)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'sources': ['channel1'],
                'related': ['channel3eee']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_channel_annotation_with_multiple_related(self):
        """
        Post a new channel of type annotation(invalid - source missing)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'sources': ['channel1'],
                'related': ['channel2', 'channel3']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Get an existing experiment
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['related'], ['channel2', 'channel3'])

        # Make sure it is symmetrical
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel2/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['related'], ['channel33'])

    def test_put_channel(self):
        """
        Update a channel (Valid - The channel exists)

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'description': 'A new channel for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_channel_source(self):
        """
        Update a channel (Valid - The channel exists)

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'description': 'A new channel for unit tests. Updated', 'default_time_sample': 1,
                'sources': ['channel2'],
                'related': ['channel3']
                }

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_channel_doesnotexist(self):
        """
        Update a channel that does not exist

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel55/'
        data = {'description': 'A new experiment for unit tests. Updated'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 404)

    def test_put_channel_name(self):
        """
        Update channel name (valid)

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1/'
        data = {'name': 'channel10'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_channel(self):
        """
        Delete a experiment

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_delete_channel_invalid(self):
        """
        Delete a channel (invalid - Violates integrity constraint because channels are linked to it)

        """

        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint64',
                'sources': ['channel1'], 'related': ['channel2']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

        # Get an existing experiment
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_channel_doesnotexist(self):
        """
        Delete a channel (invalid - The channel does not exist )

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_get_channels(self):
        """
        Get list of collections

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['channels'][0], 'channel1')
