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
from django.core.urlresolvers import resolve

from django.conf import settings

from bosscore.views import *

version = settings.BOSS_VERSION


class BossCoreManageDataRoutingTests(APITestCase):

    def test_manage_data_urls_collection_resolves(self):
        """
        Test that all manage_data urls for collections resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/manage-data/collections/')
        self.assertEqual(match.func.__name__, CollectionList.as_view().__name__)

        match = resolve('/' + version + '/manage-data/col1/')
        self.assertEqual(match.func.__name__, CollectionDetail.as_view().__name__)

    def test_manage_data_urls_experiment_resolves(self):
        """
        Test that all manage_data urls for experiments resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/manage-data/col1/experiments')
        self.assertEqual(match.func.__name__, ExperimentList.as_view().__name__)

        match = resolve('/' + version + '/manage-data/col1/exp1/')
        self.assertEqual(match.func.__name__, ExperimentDetail.as_view().__name__)

    def test_manage_data_urls_channel_layer_resolves(self):
        """
        Test that all manage_data urls for experiments resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/manage-data/col1/exp1/channels/')
        self.assertEqual(match.func.__name__, ChannelList.as_view().__name__)

        match = resolve('/' + version + '/manage-data/col1/exp1/layers/')
        self.assertEqual(match.func.__name__, LayerList.as_view().__name__)

        match = resolve('/' + version + '/manage-data/col1/exp1/channel1/')
        self.assertEqual(match.func.__name__, ChannelLayerDetail.as_view().__name__)

    def test_manage_data_urls_coordinateframes_resolves(self):
        """
        Test that all manage_data urls for coordinateframes resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/manage-data/coordinateframes')
        self.assertEqual(match.func.__name__, CoordinateFrameList.as_view().__name__)

        match = resolve('/' + version + '/manage-data/coordinateframes/cf1/')
        self.assertEqual(match.func.__name__, CoordinateFrameDetail.as_view().__name__)