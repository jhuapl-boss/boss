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

from django.conf import settings

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import force_authenticate
from rest_framework import status

from bossspatialdb.views import Downsample
from bosscore.models import Channel

from bosscore.test.setup_db import SetupTestDB
from bosscore.error import BossError
import json
from unittest.mock import patch


version = settings.BOSS_VERSION


def mock_sfn_status(a, b):
    return "RUNNING"


def mock_sfn_execute(a, b, c):
    return "ARN:abc123"


def mock_sfn_cancel(session, arn, error="Error", cause="Unknown Cause"):
    pass


class DownsampleInterfaceViewMixin(object):

    def test_get_iso_properties_no_arg(self):
        """ Test getting the properties of an isotropic channel"""
        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/downsample/col1/exp_iso/channel1/',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_iso', channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 8)
        self.assertEqual(response.data["status"], Channel.DownsampleStatus.NOT_DOWNSAMPLED)
        self.assertEqual(response.data["voxel_size"]['0'], [6.0, 6.0, 6.0])
        self.assertEqual(response.data["voxel_size"]['3'], [48.0, 48.0, 48.0])
        self.assertEqual(response.data["voxel_size"]['5'], [192.0, 192.0, 192.0])
        self.assertEqual(response.data["extent"]['0'], [2000, 5000, 200])
        self.assertEqual(response.data["extent"]['3'], [250, 625, 25])
        self.assertEqual(response.data["extent"]['5'], [63, 157, 7])
        self.assertEqual(response.data["cuboid_size"]['0'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['3'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['5'], [512, 512, 16])

    def test_get_iso_properties_iso_false(self):
        """ Test getting the properties of an isotropic channel with arg but false"""
        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/downsample/col1/exp_iso/channel1/?iso=False',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_iso', channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 8)
        self.assertEqual(response.data["status"], Channel.DownsampleStatus.NOT_DOWNSAMPLED)
        self.assertEqual(response.data["voxel_size"]['0'], [6.0, 6.0, 6.0])
        self.assertEqual(response.data["voxel_size"]['3'], [48.0, 48.0, 48.0])
        self.assertEqual(response.data["voxel_size"]['5'], [192.0, 192.0, 192.0])
        self.assertEqual(response.data["extent"]['0'], [2000, 5000, 200])
        self.assertEqual(response.data["extent"]['3'], [250, 625, 25])
        self.assertEqual(response.data["extent"]['5'], [63, 157, 7])
        self.assertEqual(response.data["cuboid_size"]['0'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['3'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['5'], [512, 512, 16])

    def test_get_iso_properties_iso(self):
        """ Test getting the properties of an isotropic channel with arg but true"""
        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/downsample/col1/exp_iso/channel1/?iso=True',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_iso', channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 8)
        self.assertEqual(response.data["status"], Channel.DownsampleStatus.NOT_DOWNSAMPLED)
        self.assertEqual(response.data["voxel_size"]['0'], [6.0, 6.0, 6.0])
        self.assertEqual(response.data["voxel_size"]['3'], [48.0, 48.0, 48.0])
        self.assertEqual(response.data["voxel_size"]['5'], [192.0, 192.0, 192.0])
        self.assertEqual(response.data["extent"]['0'], [2000, 5000, 200])
        self.assertEqual(response.data["extent"]['3'], [250, 625, 25])
        self.assertEqual(response.data["extent"]['5'], [63, 157, 7])
        self.assertEqual(response.data["cuboid_size"]['0'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['3'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['5'], [512, 512, 16])

    def test_get_aniso_properties_no_arg(self):
        """ Test getting the properties of an anisotropic channel"""
        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/downsample/col1/exp_aniso/channel1/',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_aniso', channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 8)
        self.assertEqual(response.data["status"], Channel.DownsampleStatus.NOT_DOWNSAMPLED)
        self.assertEqual(response.data["voxel_size"]['0'], [4.0, 4.0, 35.0])
        self.assertEqual(response.data["voxel_size"]['3'], [32.0, 32.0, 35.0])
        self.assertEqual(response.data["voxel_size"]['5'], [128.0, 128.0, 35.0])
        self.assertEqual(response.data["extent"]['0'], [2000, 5000, 200])
        self.assertEqual(response.data["extent"]['3'], [250, 625, 200])
        self.assertEqual(response.data["extent"]['5'], [63, 157, 200])
        self.assertEqual(response.data["cuboid_size"]['0'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['3'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['5'], [512, 512, 16])

    def test_get_aniso_properties_iso_false(self):
        """ Test getting the properties of an anisotropic channel with the iso arg false"""
        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/downsample/col1/exp_aniso/channel1/?iso=False',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_aniso', channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 8)
        self.assertEqual(response.data["status"], Channel.DownsampleStatus.NOT_DOWNSAMPLED)
        self.assertEqual(response.data["voxel_size"]['0'], [4.0, 4.0, 35.0])
        self.assertEqual(response.data["voxel_size"]['3'], [32.0, 32.0, 35.0])
        self.assertEqual(response.data["voxel_size"]['5'], [128.0, 128.0, 35.0])
        self.assertEqual(response.data["extent"]['0'], [2000, 5000, 200])
        self.assertEqual(response.data["extent"]['3'], [250, 625, 200])
        self.assertEqual(response.data["extent"]['5'], [63, 157, 200])
        self.assertEqual(response.data["cuboid_size"]['0'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['3'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['5'], [512, 512, 16])

    def test_get_aniso_properties_iso(self):
        """ Test getting the properties of an anisotropic channel with the iso arg true"""
        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/downsample/col1/exp_aniso/channel1/?iso=True',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_aniso', channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 8)
        self.assertEqual(response.data["status"], Channel.DownsampleStatus.NOT_DOWNSAMPLED)
        self.assertEqual(response.data["voxel_size"]['0'], [4.0, 4.0, 35.0])
        self.assertEqual(response.data["voxel_size"]['3'], [32.0, 32.0, 35.0])
        self.assertEqual(response.data["voxel_size"]['5'], [128.0, 128.0, 140])
        self.assertEqual(response.data["extent"]['0'], [2000, 5000, 200])
        self.assertEqual(response.data["extent"]['3'], [250, 625, 200])
        self.assertEqual(response.data["extent"]['5'], [63, 157, 50])
        self.assertEqual(response.data["cuboid_size"]['0'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['3'], [512, 512, 16])
        self.assertEqual(response.data["cuboid_size"]['5'], [512, 512, 16])

    def test_start_and_cancel_downsample_aniso(self):
        self.dbsetup.insert_downsample_data()

        factory = APIRequestFactory()
        request = factory.post('/' + version + '/downsample/col1/exp_ds_aniso/channel1/',
                               content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make Sure status has changed
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/downsample/col1/exp_ds_aniso/channel1/',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 5)
        self.assertEqual(response.data["status"], Channel.DownsampleStatus.IN_PROGRESS)

        # Cancel the downsample job
        request = factory.delete('/' + version + '/downsample/col1/exp_ds_aniso/channel1/',
                                 content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Make Sure status has changed
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/downsample/col1/exp_ds_aniso/channel1/',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Channel.DownsampleStatus.NOT_DOWNSAMPLED)

        # Try to cancel the downsample job again, but it won't because in NOT_DOWNSAMPLED state
        request = factory.delete('/' + version + '/downsample/col1/exp_ds_aniso/channel1/',
                                 content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


@patch('bossutils.aws.sfn_status', mock_sfn_status)
@patch('bossutils.aws.sfn_execute', mock_sfn_execute)
@patch('bossutils.aws.sfn_cancel', mock_sfn_cancel)
class TestDownsampleInterfaceView(DownsampleInterfaceViewMixin, APITestCase):

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        # Create a user
        self.dbsetup = SetupTestDB()
        self.user = self.dbsetup.create_user('testuser')

        # Populate DB
        self.dbsetup.insert_spatialdb_test_data()
        self.dbsetup.insert_iso_data()
