# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory
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
from unittest.mock import patch, ANY


version = settings.BOSS_VERSION


def mock_sfn_status(a, b):
    return "RUNNING"


def mock_sfn_run(a, b, c):
    return "ARN:abc123"


def mock_sfn_cancel(session, arn, error="Error", cause="Unknown Cause"):
    pass


def mock_get_account_id():
    return '184319448511'


def mock_get_region():
    return 'us-east-1'


def mock_get_session():
    return None


def mock_check_for_running_sfn(session, arn):
    return False


def mock_compute_usage_metrics(session, args, fqdn, user,
                               collection, experiment, channel):
    pass


def mock_sqs_enqueue(session, args, downsample_sqs):
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

    @patch('bossspatialdb.downsample._return_messages_to_queue', autospec=True)
    @patch('bossspatialdb.downsample._delete_message_from_queue', autospec=True)
    @patch('bossspatialdb.downsample._get_messages_from_queue', autospec=True)
    def test_start_and_cancel_downsample_aniso(self, get_msgs_mock, del_msgs_mock, ret_msgs_mock):
        chans = self.dbsetup.insert_downsample_data()

        job4 = { 'channel_id': 3874 }
        job7 = { 'channel_id': chans[0].id }
        job9 = { 'channel_id': 3999 }

        get_msgs_mock.side_effect = [
            [
                { 'MessageId': 'job4', 'ReceiptHandle': 'handle_job4', 'Body': json.dumps(job4) },
                { 'MessageId': 'job7', 'ReceiptHandle': 'handle_job7', 'Body': json.dumps(job7) },
                { 'MessageId': 'job9', 'ReceiptHandle': 'handle_job9', 'Body': json.dumps(job9) },
            ],
            [],
        ]

        exp_return_to_queue_msgs = [get_msgs_mock.side_effect[0][0], get_msgs_mock.side_effect[0][2]] 
        exp_visibility_change_payload = [
            {
                f'ChangeMessageVisibilityBatchRequestEntry.{ind+1}.Id': m['MessageId'],
                f'ChangeMessageVisibilityBatchRequestEntry.{ind+1}.ReceiptHandle': m['ReceiptHandle'],
                f'ChangeMessageVisibilityBatchRequestEntry.{ind+1}.VisibilityTimeout': 0,
            } for ind, m in enumerate(exp_return_to_queue_msgs)
        ]

        exp_del_handle = get_msgs_mock.side_effect[0][1]['ReceiptHandle']

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
        self.assertEqual(response.data["status"], Channel.DownsampleStatus.QUEUED)

        # Cancel the downsample job
        request = factory.delete('/' + version + '/downsample/col1/exp_ds_aniso/channel1/',
                                 content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1')
        get_msgs_mock.assert_called_once_with(ANY)
        del_msgs_mock.assert_called_once_with(ANY, exp_del_handle)
        ret_msgs_mock.assert_called_once_with(ANY, exp_visibility_change_payload)
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


@patch('bossspatialdb.downsample._sqs_enqueue', mock_sqs_enqueue)
@patch('bossspatialdb.downsample.compute_usage_metrics', mock_compute_usage_metrics)
@patch('bossspatialdb.downsample.check_for_running_sfn', mock_check_for_running_sfn)
@patch('bossspatialdb.downsample.get_session', mock_get_session)
@patch('bossspatialdb.downsample.get_region', mock_get_region)
@patch('bossspatialdb.downsample.get_account_id', mock_get_account_id)
@patch('bossutils.aws.get_session', mock_get_session)
@patch('bossutils.aws.sfn_status', mock_sfn_status)
@patch('bossutils.aws.sfn_run', mock_sfn_run)
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
