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
from rest_framework.test import APIRequestFactory

from ..request import BossRequest
from ..views import BossMeta
from .setup_db import setupTestDB
from ..error import BossError

from django.conf import settings
from django.contrib.auth.models import User

version = settings.BOSS_VERSION


class BossCoreMetaRequestTests(APITestCase):
    """
    Class to test invalid requests for the meta data service
    """

    def setUp(self):
        """
        Initialize the test database with some objects
        :return:
        """
        self.rf = APIRequestFactory()
        # col = Collection.objects.create(name='col1')
        # cf = CoordinateFrame.objects.create(name='cf1', description='cf1',
        #                                     x_start=0, x_stop=1000,
        #                                     y_start=0, y_stop=1000,
        #                                     z_start=0, z_stop=1000,
        #                                     x_voxel_size=4, y_voxel_size=4, z_voxel_size=4,
        #                                     time_step=1
        #                                     )
        # exp = Experiment.objects.create(name='exp1', collection=col, coord_frame=cf)
        # channel = ChannelLayer.objects.create(name='channel1', experiment=exp, is_channel=True, default_time_step=1)
        # layer = ChannelLayer.objects.create(name='layer1', experiment=exp, is_channel=False, default_time_step=1)
        #
        # channel = ChannelLayer.objects.create(name='channel2', experiment=exp, is_channel=True, default_time_step=1)
        # layer = ChannelLayer.objects.create(name='layer2', experiment=exp, is_channel=False, default_time_step=1)

        user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup = setupTestDB()
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()
    def test_bossrequest_collection_not_found(self):
        """
        Test initialization of requests with a collection that does not exist
        :return:
        """
        # create the request with collection name
        url = '/' + version + '/meta/col2/?key=mkey'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        try:
            ret = BossRequest(drfrequest)
        except BossError as err:
            assert err.args[0] == 404

    def test_bossrequest_experiment_not_found(self):
        """
        Test initialization of requests with a collection that does not exist
        :return:
        """
        # create the request with collection name
        url = '/' + version + '/meta/col1/exp2/?key=mkey'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        try:
            ret = BossRequest(drfrequest)
        except BossError as err:
            assert err.args[0] == 404

    def test_bossrequest_channel_layer_not_found(self):
        """
        Test initialization of requests with a collection that does not exist
        :return:
        """
        # create the request with collection name
        url = '/' + version + '/meta/col1/exp1/channel2/?key=mkey'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        try:
            ret = BossRequest(drfrequest)
        except BossError as err:
            assert err.args[0] == 404
