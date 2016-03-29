import blosc
import numpy as np

from django.conf import settings
from django.core.urlresolvers import resolve
from django.http import HttpRequest

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.request import Request

from ..views import CutoutView, Cutout

from bosscore.request import BossRequest

from project import BossResourceDjango

from .setup_db import SetupTestDB


version = settings.BOSS_VERSION


class TestDjangoResource(APITestCase):

    def setUp(self):
        """Setup test by inserting data model items into the database"""
        SetupTestDB.insert_test_data()

        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        channel = 'channel1'
        boss_key = 'col1&exp1&channel1&0'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version

        self.request_channel = BossRequest(drfrequest)

    def test_basic_resource_col(self):
        """Test basic get collection interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        col = resource.get_collection()

        assert col.name == self.request_channel.collection['name']
        assert col.description == self.request_channel.collection['name']

    def test_basic_resource_coord_frame(self):
        """Test basic get coordinate frame interface

        Returns:
            None

        """
        setup_data = self.get_image_dict()
        resource = BossResourceBasic(setup_data)

        coord = resource.get_coord_frame()

        assert coord.name == setup_data['coord_frame']['name']
        assert coord.description == setup_data['coord_frame']['description']
        assert coord.x_start == setup_data['coord_frame']['x_start']
        assert coord.x_stop == setup_data['coord_frame']['x_stop']
        assert coord.y_start == setup_data['coord_frame']['y_start']
        assert coord.y_stop == setup_data['coord_frame']['y_stop']
        assert coord.z_start == setup_data['coord_frame']['z_start']
        assert coord.z_stop == setup_data['coord_frame']['z_stop']
        assert coord.x_voxel_size == setup_data['coord_frame']['x_voxel_size']
        assert coord.y_voxel_size == setup_data['coord_frame']['y_voxel_size']
        assert coord.z_voxel_size == setup_data['coord_frame']['z_voxel_size']
        assert coord.voxel_unit == setup_data['coord_frame']['voxel_unit']
        assert coord.time_step == setup_data['coord_frame']['time_step']
        assert coord.time_step_unit == setup_data['coord_frame']['time_step_unit']

    def test_basic_resource_experiment(self):
        """Test basic get experiment interface

        Returns:
            None

        """
        setup_data = self.get_image_dict()
        resource = BossResourceBasic(setup_data)

        exp = resource.get_experiment()

        assert exp.name == setup_data['experiment']['name']
        assert exp.description == setup_data['experiment']['description']
        assert exp.num_hierarchy_levels == setup_data['experiment']['num_hierarchy_levels']
        assert exp.hierarchy_method == setup_data['experiment']['hierarchy_method']

    def test_basic_resource_channel_no_time(self):
        """Test basic get channel interface

        Returns:
            None

        """
        setup_data = self.get_image_dict()
        resource = BossResourceBasic(setup_data)

        assert resource.is_channel() == True

        assert not resource.get_layer()

        channel = resource.get_channel()
        assert channel.name == setup_data['channel_layer']['name']
        assert channel.description == setup_data['channel_layer']['description']
        assert channel.datatype == setup_data['channel_layer']['datatype']
        assert channel.max_time_step == setup_data['channel_layer']['max_time_step']

    def test_basic_resource_layer_no_time(self):
        """Test basic get layer interface

        Returns:
            None

        """
        setup_data = self.get_image_dict()
        setup_data['channel_layer']['name'] = "layer1"
        setup_data['channel_layer']['description'] = "Test layer 1"
        setup_data['channel_layer']['is_channel'] = False
        setup_data['channel_layer']['layer_map'] = ['ch1']
        resource = BossResourceBasic(setup_data)

        assert resource.is_channel() == False

        assert not resource.get_channel()

        channel = resource.get_layer()
        assert channel.name == setup_data['channel_layer']['name']
        assert channel.description == setup_data['channel_layer']['description']
        assert channel.datatype == setup_data['channel_layer']['datatype']
        assert channel.max_time_step == setup_data['channel_layer']['max_time_step']
        assert channel.parent_channels == setup_data['channel_layer']['layer_map']

    def test_basic_resource_time_samples(self):
        """Test basic get and set time samples interface

        Returns:
            None

        """
        setup_data = self.get_image_dict()
        resource = BossResourceBasic(setup_data)

        assert resource.is_channel() == True

        assert resource.get_time_samples() == [0]

        resource.set_time_samples([0, 1, 2, 3, 4, 5])
        assert resource.get_time_samples() == [0, 1, 2, 3, 4, 5]

        resource.set_time_samples(3)
        assert resource.get_time_samples() == [3]

    def test_basic_resource_get_boss_key(self):
        """Test basic get boss key interface

        Returns:
            None

        """
        setup_data = self.get_image_dict()
        resource = BossResourceBasic(setup_data)

        assert resource.get_boss_key() == setup_data['boss_key']

    def test_basic_resource_get_lookup_key(self):
        """Test basic get lookup key interface

        Returns:
            None

        """
        setup_data = self.get_image_dict()
        resource = BossResourceBasic(setup_data)

        assert resource.get_lookup_key() == setup_data['lookup_key']

    def test_basic_resource_get_data_type(self):
        """Test basic get datatype interface

        Returns:
            None

        """
        setup_data = self.get_image_dict()
        resource = BossResourceBasic(setup_data)

        assert resource.get_data_type() == setup_data['channel_layer']['datatype']


#class CutoutInterfaceViewTests(APITestCase):
#    # TODO: Add proper view tests once cache is integrated, currently just making sure you get the right statuscode back
#
#    def setUp(self):
#        """
#        Initialize the database
#        :return:
#        """
#        setupTestDB.insert_test_data()
#
#    def test_full_token_cutout_post(self):
#        """
#        Test to make sure posting a block of data returns a 201
#        :return:
#        """
#        a = np.random.randint(0, 100, (5, 6, 2))
#        h = a.tobytes()
#        bb = blosc.compress(h, typesize=8)
#
#        response = self.client.post('/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2', bb,
#                                    content_type='application/octet-stream')
#
#        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#    def test_view_token_cutout_post(self):
#        """
#        Test to make sure posting a block of data returns a 201
#        :return:
#        """
#        a = np.random.randint(0, 100, (5, 6, 2))
#        h = a.tobytes()
#        bb = blosc.compress(h, typesize=8)
#
#        response = self.client.post('/' + version + '/cutout/2/0:5/0:6/0:2?view=token1', bb,
#                                    content_type='application/octet-stream')
#
#        # TODO: Once views are implemented need to finish test and switch to 200
#        #self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#
#    def test_full_token_cutout_get(self):
#        """
#        Test to make sure getting a block of data returns a 200
#        :return:
#        """
#        response = self.client.get('/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2',
#                                   content_type='application/octet-stream')
#
#        self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#    def test_view_token_cutout_get(self):
#        """
#        Test to make sure getting a block of data returns a 200
#        :return:
#        """
#        response = self.client.get('/' + version + '/cutout/2/0:5/0:6/0:2?view=token1',
#                                   content_type='application/octet-stream')
#
#        # TODO: Once views are implemented need to finish test and switch to 200
#        #self.assertEqual(response.status_code, status.HTTP_200_OK)
#        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#
#    def test_view_token_cutout_get_missing_token_error(self):
#        """
#        Test to make sure you get an error
#        :return:
#        """
#        response = self.client.get('/' + version + '/cutout/2/0:5/0:6/0:2',
#                                   content_type='application/octet-stream')
#
#        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#