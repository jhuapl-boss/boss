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
from .setup_db import SetupTestDB, TEST_DATA_EXPERIMENTS
from bosscore.models import Channel

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

    def test_flag_delete_collection(self):
        """
        Delete a collection (valid- Check that the flag is set correctly)

        """
        url = '/' + version + '/collection/col55/'
        data = {'description': 'A new collection for unit tests'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Get on a deleted collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_collection_invalid(self):
        """
        Delete a collection (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/collection/col1/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

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
                'num_hierarchy_levels': 10, 'hierarchy_method': 'isotropic', 'num_time_samples': 10}
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
                'num_hierarchy_levels': 10, 'hierarchy_method': 'isotropic', 'num_time_samples': 10}
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
                'num_hierarchy_levels': 10, 'hierarchy_method': 'anisotropic', 'num_time_samples': 10, 'dummy': 'dummy'}
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
                'num_hierarchy_levels': 10, 'hierarchy_method': 'anisotropic'}
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
                'num_hierarchy_levels': 10, 'hierarchy_method': 'anisotropic', 'num_time_samples': 10}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_experiment_with_time_step(self):
        """
        Post a new experiment (valid _ the post has all the required data and does not already exist and includes
        timestep)

        """
        # Get the coordinate frame id
        url = '/' + version + '/coord/cf1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cf = response.data['name']

        # Post a new experiment
        url = '/' + version + '/collection/col1/experiment/exp2'
        data = {'description': 'This is a new experiment', 'coord_frame': cf,
                'num_hierarchy_levels': 10, 'hierarchy_method': 'anisotropic', 'num_time_samples': 10,
                'time_step': 1, 'time_step_unit': 'nanoseconds'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

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
                'num_hierarchy_levels': 10, 'hierarchy_method': 'isotropic', 'num_time_samples': 10}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp2'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)
        self.assertEquals((response.json())['code'], 4005)

    def test_delete_experiment_invalid(self):
        """
        Delete a experiment (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/collection/col1/experiment/exp1/'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

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
        self.assertCountEqual(response.data['experiments'], TEST_DATA_EXPERIMENTS)


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

    def test_get_coordinateframes_owner(self):

        """
        Get list of coordinateframes

        """
        url = '/' + version + '/coord/?owner=True'

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
                'time_step_unit': 'nanoseconds'}

        # Get an existing collection
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_coordinateframe_already_exists(self):
        """
        Post a new coordinate frame (invalid - Name already exists)

        """
        url = '/' + version + '/coord/cf1'
        data = {'description': 'This is a test coordinateframe', 'x_start': 0, 'x_stop': 1000,
                'y_start': 0, 'y_stop': 1000, 'z_start': 0, 'z_stop': 1000,
                'x_voxel_size': 4, 'y_voxel_size': 4, 'z_voxel_size': 4, 'voxel_unit': 'nanometers',
                'time_step_unit': 'nanoseconds'}

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

        # Get on the resource should return an error since it is marked for deleton
        response = self.client.get(url)
        resp = response.json()
        self.assertEquals(resp['code'], 4005)

        url = '/' + version + '/coord/cf1/'
        response = self.client.delete(url)
        resp = response.json()
        self.assertEqual(resp['code'], 4003)

    def test_delete_coordinateframe_invalid(self):
        """
        Delete a collection (invalid - Violates integrity constraint)

        """
        url = '/' + version + '/coord/cf1/'

        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

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
        self.super_user = dbsetup.create_super_user()
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
        self.assertEqual(response.data['downsample_status'], 'NOT_DOWNSAMPLED')

    def test_post_channel(self):
        """
        Post a new channel (Valid - the post has all the required data and does not already exist)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_post_channel_set_cloudvol_storage_no_cv_path(self):
        """
        When using CloudVolume storage type w/o providing cv_path, cv_path
        should default to /{coll}/{exp}/{chan}.
        """
        coll = 'col1'
        exp = 'exp1'
        chan = 'channel10'
        url = '/' + version + f'/collection/{coll}/experiment/{exp}/channel/{chan}/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image',
                'storage_type': Channel.StorageType.CLOUD_VOLUME}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['cv_path'], f'/{coll}/{exp}/{chan}')

    def test_post_channel_set_bucket_forbidden_for_non_admins(self):
        """
        Only admins should be able to set the bucket name.
        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image', 'bucket': 'my.bucket.boss'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_post_channel_set_bucket_as_admin(self):
        """
        Only admins should be able to set the bucket name.
        """
        self.client.force_login(self.super_user)
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        bucket_name = 'my.bucket.boss'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image', 'bucket': bucket_name}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['bucket'], bucket_name)

    def test_post_channel_spdb_with_cv_path(self):
        """
        Setting cv_path when storage_type != CloudVolume is invalid.
        """
        self.client.force_login(self.super_user)
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image',
                'cv_path': '/custom/cv', 'storage_type': Channel.StorageType.SPDB}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_post_channel_cloudvol_with_cv_path_forbidden_when_not_admin(self):
        """
        Setting cv_path is isvalid when not an admin.
        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image',
                'cv_path': '/custom/cv', 'storage_type': Channel.StorageType.CLOUD_VOLUME}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_post_channel_cloudvol_with_cv_path_as_admin(self):
        """
        Setting cv_path when storage_type == CloudVolume is valid when done as admin.
        """
        self.client.force_login(self.super_user)
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        cv_path = '/custom/cv'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image',
                'cv_path': cv_path, 'storage_type': Channel.StorageType.CLOUD_VOLUME}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['cv_path'], cv_path)

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
        Post a new channel of type annotation w/o providing a source channel.
        This used to be forbidden but we decided to allow this.
        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

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

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_channel_set_cv_path_forbidden_for_non_admins(self):
        """
        Update a channel (Invalid - only admins can set cv_path)

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'cv_path': '/my/custom/cv/dataset'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_channel_set_cv_path_as_admin(self):
        """
        Update a channel's bucket (Valid - admins can set cv_path)

        """
        self.client.force_login(self.super_user)
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'cv_path': '/my/custom/cv/dataset'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_channel_set_bucket_forbidden_for_non_admins(self):
        """
        Update a channel (Invalid - only admins can set the bucket name)

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'bucket': 'new.bucket.boss'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_channel_set_bucket_as_admin(self):
        """
        Update a channel's bucket (Valid - admins can set the bucket name)

        """
        self.client.force_login(self.super_user)
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'bucket': 'new.bucket.boss'}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_channel_set_storage_type_forbidden_for_non_admins(self):
        """
        Update a channel (Invalid - only admins can set the storage type after creation)

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'storage_type': Channel.StorageType.CLOUD_VOLUME}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_channel_set_storage_type_as_admin(self):
        """
        Update a channel's storage type (Valid - admins can change this after creation)

        """
        self.client.force_login(self.super_user)
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'storage_type': Channel.StorageType.CLOUD_VOLUME}

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_channel_source(self):
        """
        Update a channel (Valid - The channel exists)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'sources': ['channel1'],
                'related': ['channel2', 'channel3']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1'
        data = {'description': 'A new channel for unit tests. Updated', 'default_time_sample': 1,
                'sources': ['channel2'],
                'related': ['channel3']
                }

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_channel_downsample(self):
        """
        Try to update a downsample property of the channel but you can't

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'sources': ['channel1'],
                'related': ['channel2', 'channel3']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        data = {'downsample_status': 'DOWNSAMPLED'}
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 400)

        data = {'downsample_arn': 'asdfasfasdf'}
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_put_channel_remove_source(self):
        """
        Update a channel (Valid - The channel exists)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'sources': ['channel1', 'channel2']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Get an existing channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['sources']), {'channel1', 'channel2'})

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33'
        data = {'description': 'A new channel for unit tests. Updated', 'sources': ['channel2']}
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

        # Get an existing channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['sources']), {'channel2'})

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33'
        data = {'description': 'A new channel for unit tests. Updated', 'sources': []}
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

        # Get an existing channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['sources'], [])

    def test_put_channel_remove_related(self):
        """
        Update a channel (Valid - The channel exists)

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'image', 'datatype': 'uint8',
                'related': ['channel1', 'channel2']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Get an existing channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['related']), {'channel1', 'channel2'})

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33'
        data = {'description': 'A new channel for unit tests. Updated', 'related': ['channel2']}
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

        # Get an existing channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data['related']), {'channel2'})

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
        Delete a channel

        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10/'
        data = {'description': 'This is a new channel', 'datatype': 'uint8', 'type': 'image'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel10'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)
        self.assertEquals((response.json())['code'], 4005)

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
        self.assertEqual(response.status_code, 400)

        # Ensure channel still exists
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_channel_ignore_derived_channels_marked_for_deletion(self):
        """
        Delete a channel (allow when all derived channels are marked for deletion)

        """

        # Post new channels
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel11/'
        data = {'description': 'This is a new source channel', 'type': 'image', 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel22/'
        data = {'description': 'This is a new related channel', 'type': 'image', 'datatype': 'uint8'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint64',
                'sources': ['channel11'], 'related': ['channel22']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        # Delete the new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        response = self.client.delete(url, data=data)
        self.assertEqual(response.status_code, 204)

        # Delete the source channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel11'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Delete the related channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel22'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

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

        # Get an existing channel
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['channels'][0], 'channel1')
