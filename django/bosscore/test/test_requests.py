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
from rest_framework.test import force_authenticate
from rest_framework.test import APIRequestFactory

from django.conf import settings
from django.contrib.auth.models import User
import numpy as np

from ..request import BossRequest
from bosscore.error import BossError
from .setup_db import SetupTestDB, NUM_HIERARCHY_LEVELS, BASE_RESOLUTION, EXP1, EXP_BASE_RES, CHAN_BASE_RES
from bossspatialdb.views import Cutout

version = settings.BOSS_VERSION


class CutoutRequestTests(APITestCase):
    """
    Class to test boss requests
    """

    def setUp(self):
        """
            Initialize the database
            :return:
        """
        self.rf = APIRequestFactory()
        dbsetup = SetupTestDB()
        user = dbsetup.create_super_user(username='testuser', email='test@test.com', password='testuser')
        dbsetup.set_user(user)
        self.user = user
        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_request_cutout_init_channel(self):
        """
        Test initialization of cutout requests for the datamodel
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        channel = 'channel1'
        boss_key = 'col1&exp1&channel1'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": exp,
            "channel_name": channel,
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        ret = BossRequest(drfrequest, request_args)
        self.assertEqual(ret.get_collection(), col)
        self.assertEqual(ret.get_experiment(), exp)
        self.assertEqual(ret.get_channel(), channel)
        self.assertEqual(ret.get_boss_key(), boss_key)
        self.assertEqual(ret.time_request, False)

    def test_request_cutout_init_cutoutargs_channel(self):
        """
        Test initialization of cutout arguments for a cutout request
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'

        res = 2
        (x_start, x_stop) = (0, 5)
        (y_start, y_stop) = (0, 6)
        (z_start, z_stop) = (0, 2)

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel1',
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }
        ret = BossRequest(drfrequest, request_args)

        self.assertEqual(ret.get_resolution(), res)
        self.assertEqual(ret.get_x_start(), x_start)
        self.assertEqual(ret.get_x_stop(), x_stop)
        self.assertEqual(ret.get_x_span(), x_stop - x_start)

        self.assertEqual(ret.get_y_start(), y_start)
        self.assertEqual(ret.get_y_stop(), y_stop)
        self.assertEqual(ret.get_y_span(), y_stop - y_start)

        self.assertEqual(ret.get_z_start(), z_start)
        self.assertEqual(ret.get_z_stop(), z_stop)
        self.assertEqual(ret.get_z_span(), z_stop - z_start)

    def test_request_cutout_init_cutoutargs_no_time(self):
        """
        Test initialization of timesample arguments  without a specific timesample
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel1',
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }
        ret = BossRequest(drfrequest, request_args)
        time = ret.get_time()
        self.assertEqual(time, range(0, 1))

    def test_request_cutout_init_cutoutargs_time_range(self):
        """
        Test initialization of boss_key for a time sample range
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/1:5/'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel1',
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": "1:5"
        }

        ret = BossRequest(drfrequest, request_args)
        time = ret.get_time()
        self.assertEqual(time, range(1, 5))
        self.assertEqual(ret.time_request, True)

    def test_request_cutout_lookupkey(self):
        """
        Test initialization of boss_key for a time sample range
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/1:5/'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel1',
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": "1:5"
        }

        ret = BossRequest(drfrequest, request_args)
        col_id = ret.collection.pk
        exp_id = ret.experiment.pk
        channel_id = ret.channel.pk
        base_lookup = str(col_id) + '&' + str(exp_id) + '&' + str(channel_id)
        self.assertEqual(base_lookup, ret.get_lookup_key())

    def test_request_cutout_filter_time(self):
        """
        Test initialization of boss_key for a time sample range
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel3/2/0:5/0:6/0:2/1:5/?filter=1,2,3,4'
        expected_ids = np.array([1, 2, 3, 4])
        expected_ids = expected_ids.astype(np.uint64)

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel3',
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": "1:5",
            "ids": '1,2,3,4'
        }

        ret = BossRequest(drfrequest, request_args)
        self.assertEqual(np.array_equal(ret.get_filter_ids(), expected_ids), True)

    def test_request_cutout_filter_single_id(self):
        """
        Test initialization of boss_key for a time sample range
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel3/2/0:5/0:6/0:2/1:5/?filter=1'
        expected_ids = np.array([1]).astype(np.uint64)

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel3',
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": "1:5",
            "ids": '1'
        }

        ret = BossRequest(drfrequest, request_args)
        self.assertEqual(np.array_equal(ret.get_filter_ids(), expected_ids), True)

    def test_request_cutout_filter_no_time(self):
        """
        Test initialization of boss_key for a time sample range
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel3/2/0:5/0:6/0:2/?filter=1,2,3,4'
        expected_ids = np.array([1, 2, 3, 4])
        expected_ids = expected_ids.astype(np.uint64)

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel3',
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None,
            "ids": '1,2,3,4'
        }

        ret = BossRequest(drfrequest, request_args)
        self.assertEqual(np.array_equal(ret.get_filter_ids(),expected_ids),True)


    def test_request_cutout_filter_invalid_channel_type(self):
        """
        Test initialization of cutout arguments for a invalid cutout request. The x-args are outside the coordinate
        frame
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/0/0:10/0:6/0:2/?filter=1'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel1',
            "resolution": 2,
            "x_args": "0:10",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None,
            "ids": "1"
        }
        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_filter_invalid_ids(self):
        """
        Test initialization of cutout arguments for a invalid cutout request. The x-args are outside the coordinate
        frame
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/0/0:10/0:6/0:2/?filter=1,foo'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel1',
            "resolution": 2,
            "x_args": "0:10",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None,
            "ids": "1, foo"
        }
        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)


    def test_request_cutout_invalid_xargs(self):
        """
        Test initialization of cutout arguments for a invalid cutout request. The x-args are outside the coordinate
        frame
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/0/990:1010/0:6/0:2/'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel1',
            "resolution": 2,
            "x_args": "990:1010",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }
        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_invalid_yargs(self):
        """
        Test initialization of cutout arguments for a invalid cutout request. The x-args are outside the coordinate
        frame
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/0/0:6/0:1010/0:2/'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version
        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": 'col1',
            "experiment_name": 'exp1',
            "channel_name": 'channel1',
            "resolution": 2,
            "x_args": "0:6",
            "y_args": "0:1010",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_invalid_zargs(self):
        """
        Test initialization of cutout arguments for a invalid cutout request. The x-args are outside the coordinate
        frame
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/0/0:6/0:6/0:1040/'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel1",
            "resolution": 2,
            "x_args": "0:6",
            "y_args": "0:6",
            "z_args": "0:1040",
            "time_args": None
        }
        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)


class CutoutInvalidRequestTests(APITestCase):
    """
    Class to test boss invalid requests
    """

    def setUp(self):
        """
            Initialize the database
            :return:
        """
        self.rf = APIRequestFactory()
        dbsetup = SetupTestDB()
        dbsetup.create_super_user()

        user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup.set_user(user)
        dbsetup.add_role('resource-manager')
        self.user = user
        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_request_cutout_invalid_collection(self):
        """
        Test initialization of cutout requests for an invalid datamode - Collection does not exist
        :return:
        """
        url = '/' + version + '/cutout/col5786/exp1/channel1/2/0:5/0:6/0:2/'
        col = 'col5786'
        exp = 'exp1'
        channel = 'channel1'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": exp,
            "channel_name": channel,
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_invalid_experiment(self):
        """
        Test initialization of cutout requests for an invalid datamodel - Experiment does not exist
        :return:
        """
        url = '/' + version + '/cutout/col1/exp56668/channel1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp56668'
        channel = 'channel1'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": exp,
            "channel_name": channel,
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_invalid_channel(self):
        """
        Test initialization of cutout requests for an invalid datamodel - Channel does not exist
        :return:
        """
        url = '/' + version + '/cutout/col1/exp56668/channel1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        channel = 'channel133323'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": exp,
            "channel_name": channel,
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_invalid_datamodel(self):
        """
        Test initialization of cutout requests for an invalid datamodel - experiment  does not exist for the collection
        :return:
        """
        url = '/' + version + '/cutout/col2/exp1/channel1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        channel = 'channel12345'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": exp,
            "channel_name": channel,
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_resolution_within_range(self):
        """
        Test initialization of cutout requests with a valid resolution
        """
        col = 'col1'
        channel = 'channel1'
        res = NUM_HIERARCHY_LEVELS-1
        url = '/{}/cutout/{}/{}/{}/{}/0:5/0:6/0:2/'.format(version, col, EXP1, channel, res)

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": EXP1,
            "channel_name": channel,
            "resolution": res,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        # Should not raise BossError.
        BossRequest(drfrequest, request_args)

    def test_request_cutout_invalid_resolution_past_upper_bound(self):
        """
        Test initialization of cutout requests with an invalid resolution
        """
        col = 'col1'
        channel = 'channel1'
        res = NUM_HIERARCHY_LEVELS
        url = '/{}/cutout/{}/{}/{}/{}/0:5/0:6/0:2/'.format(version, col, EXP1, channel, res)

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": EXP1,
            "channel_name": channel,
            "resolution": res,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_valid_base_resolution(self):
        """
        Test cutout request when channel has a non-zero base resolution
        """
        col = 'col1'
        channel = CHAN_BASE_RES
        res = NUM_HIERARCHY_LEVELS + BASE_RESOLUTION - 1
        url = '/{}/cutout/{}/{}/{}/{}/0:5/0:6/0:2/'.format(version, col, EXP_BASE_RES, channel, res)

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": EXP_BASE_RES,
            "channel_name": channel,
            "resolution": res,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        # No exception should be raised.
        BossRequest(drfrequest, request_args)

    def test_request_cutout_invalid_base_resolution_below_lower_bound(self):
        """
        Test cutout request when channel has a non-zero base resolution - pass
        resolution less than the base resolution
        """
        col = 'col1'
        channel = CHAN_BASE_RES
        res = BASE_RESOLUTION - 1
        url = '/{}/cutout/{}/{}/{}/{}/0:5/0:6/0:2/'.format(version, col, EXP_BASE_RES, channel, res)

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": EXP_BASE_RES,
            "channel_name": channel,
            "resolution": res,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_invalid_base_resolution_above_upper_bound(self):
        """
        Test cutout request when channel has a non-zero base resolution - pass
        resolution equal to the base resolution + num hierarchy levels
        """
        col = 'col1'
        channel = CHAN_BASE_RES
        res = BASE_RESOLUTION + NUM_HIERARCHY_LEVELS
        url = '/{}/cutout/{}/{}/{}/{}/0:5/0:6/0:2/'.format(version, col, EXP_BASE_RES, channel, res)

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": EXP_BASE_RES,
            "channel_name": channel,
            "resolution": res,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_cutout_invalid_deleted_channel(self):
        """
        Test initialization of cutout requests for channel that was just deleted
        """
        # Post a new channel
        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint64',
                'sources': ['channel1'], 'related': ['channel2']}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        url = '/' + version + '/cutout/col2/exp1/channel33/0/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        channel = 'channel33'

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = Cutout().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "service": "cutout",
            "version": version,
            "collection_name": col,
            "experiment_name": exp,
            "channel_name": channel,
            "resolution": 0,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)


