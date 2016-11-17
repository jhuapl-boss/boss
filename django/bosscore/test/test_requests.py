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

from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth.models import User

from ..request import BossRequest
from bosscore.error import BossError
from .setup_db import SetupTestDB
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
        user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup = SetupTestDB()
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
        user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup = SetupTestDB()
        dbsetup.set_user(user)
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

    def test_request_cutout_invalid_resolution(self):
        """
        Test initialization of cutout requests for an invalid datamodel - experiment  does not exist for the collection
        :return:
        """
        url = '/' + version + '/cutout/col2/exp1/channel1/92/0:5/0:6/0:2/'
        col = 'col1'
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
            "resolution": 92,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "0:2",
            "time_args": None
        }

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)
