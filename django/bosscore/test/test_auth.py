from rest_framework.test import APITestCase
from django.conf import settings
from .setup_db import SetupTestDB

version = settings.BOSS_VERSION


class UserPermissionsCollection(APITestCase):
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

        # Create a new user with different objects
        user2 = dbsetup.create_user('testuser1')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(user2)
        self.client.force_login(user2)
        dbsetup.add_collection("unittestcol", "testcollection")

    def test_get_collection_no_permission(self):
        """
        Get a collection that does not exist

        """
        url = '/' + version + '/collection/col1/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_collection_valid_permission(self):
        """
        Get a valid collection

        """
        url = '/' + version + '/collection/unittestcol/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'unittestcol')

    # TODO Add unit test for POST ??

    def test_put_collection_no_permissions(self):
        """
        Update a collection for which the user does not have update permissions on

        """
        url = '/' + version + '/collection/col1/'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_put_collection_valid_permission(self):
        """
        Update a collection that  the user has permissions on

        """
        url = '/' + version + '/collection/unittestcol/'
        data = {'description': 'A new collection for unit tests. Updated'}

        # Get an existing collection
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_put_collection_name_valid_permission(self):
        """
        Update collection name (valid)

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
        # Get an existing collection
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_collection_valid_permission(self):
        """
        Delete a collection that the user has permission for

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
        self.assertEqual(response.data[0], 'unittestcol')
        self.assertEqual(len(response.data), 1)


class UserPermissionsCoordinateFrame(APITestCase):
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

        # Create a new user with different objects
        user2 = dbsetup.create_user('testuser1')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(user2)
        self.client.force_login(user2)
        dbsetup.add_coordinate_frame('unittestcf', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4, 1)

    def test_get_coordinate_frame_no_permission(self):
        """
        Get a coordinate frame that the user has no permissions for

        """
        url = '/' + version + '/coord/cf1/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_coordinate_frame_valid_permission(self):
        """
        Get a valid coordinate_frame

        """
        url = '/' + version + '/coord/unittestcf/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'unittestcf')

    # TODO Add unit test for POST ??

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
        Delete a coordinate frame that the user does not have permission for

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
        self.assertEqual(response.data[0], 'unittestcf')
        self.assertEqual(len(response.data), 1)


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

        # Create a new user with different objects
        user2 = dbsetup.create_user('testuser1')
        dbsetup.set_user(user2)
        dbsetup.add_role('resource-manager')
        self.client.force_login(user2)
        dbsetup.add_collection("unittestcol", "testcollection")
        dbsetup.add_coordinate_frame('unittestcf', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4, 1)
        dbsetup.add_experiment('unittestcol', 'unittestexp', 'unittestcf', 10, 10)

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
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'max_time_sample': 10, 'dummy': 'dummy'}
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
                'num_hierarchy_levels': 10, 'hierarchy_method': 'slice', 'max_time_sample': 10, 'dummy': 'dummy'}
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
        self.assertEqual(response.data, [])

    def test_get_experiments(self):
        """
        Get list of experiments

        """
        url = '/' + version + '/collection/unittestcol/experiment/'

        # Get an existing collection
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0], 'unittestexp')
        self.assertEqual(len(response.data), 1)


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

        # Create a new user with different objects
        user2 = dbsetup.create_user('testuser1')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(user2)
        self.client.force_login(user2)
        dbsetup.add_collection("unittestcol", "testcollection")
        dbsetup.add_coordinate_frame('unittestcf', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4, 1)
        dbsetup.add_experiment('unittestcol', 'unittestexp', 'unittestcf', 10, 10)

        dbsetup.add_channel('unittestcol', 'unittestexp', 'unittestchannel', 0, 0, 'uint8')
        dbsetup.add_channel('unittestcol', 'unittestexp', 'unittestlayer', 0, 0, 'uint16', 'annotation')
        #dbsetup.add_channel_layer_map('unittestcol', 'unittestexp', 'unittestchannel', 'unittestlayer')

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

    def test_get_channels_no_permissions(self):
        """
        Get list of channels

        """
        url = '/' + version + '/collection/col1/experiment/exp1/channel/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_get_channels(self):
        """
        Get list of channels

        """
        url = '/' + version + '/collection/unittestcol/experiment/unittestexp/channel/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0], 'unittestchannel')
