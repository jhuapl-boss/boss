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

from bosscore.views.views_resource import CollectionList, CollectionDetail, ExperimentList, ExperimentDetail, \
    ChannelList, ChannelDetail, CoordinateFrameList, CoordinateFrameDetail
from bosscore.views.views_permission import ResourceUserPermission
from bosscore.views.views_group import BossGroupMember, BossGroup
from bosscore.views.views_user import BossUserRole, BossUser, BossUserGroups


version = 'v0.7'


class BossCoreResourceRoutingTests(APITestCase):

    def test_manage_data_urls_collection_resolves(self):
        """
        Test that all manage_data urls for collections resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/collection/')
        self.assertEqual(match.func.__name__, CollectionList.as_view().__name__)

        match = resolve('/' + version + '/collection/col1/')
        self.assertEqual(match.func.__name__, CollectionDetail.as_view().__name__)

    def test_manage_data_urls_experiment_resolves(self):
        """
        Test that all manage_data urls for experiments resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/collection/col1/experiment')
        self.assertEqual(match.func.__name__, ExperimentList.as_view().__name__)

        match = resolve('/' + version + '/collection/col1/experiment/exp1/')
        self.assertEqual(match.func.__name__, ExperimentDetail.as_view().__name__)

    def test_manage_data_urls_channel_layer_resolves(self):
        """
        Test that all manage_data urls for experiments resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/collection/col1/experiment/exp1/channel/')
        self.assertEqual(match.func.__name__, ChannelList.as_view().__name__)

        match = resolve('/' + version + '/collection/col1/experiment/exp1/channel/channel1/')
        self.assertEqual(match.func.__name__, ChannelDetail.as_view().__name__)


    def test_manage_data_urls_coordinateframes_resolves(self):
        """
        Test that all manage_data urls for coordinateframes resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/coord/')
        self.assertEqual(match.func.__name__, CoordinateFrameList.as_view().__name__)

        match = resolve('/' + version + '/coord/cf1/')
        self.assertEqual(match.func.__name__, CoordinateFrameDetail.as_view().__name__)

class BossCorePermissionRoutingTests(APITestCase):

    def test_permission_collection_resolves(self):
        """
        Test that all permission urls for collections resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/permission/test/col1/')
        self.assertEqual(match.func.__name__, ResourceUserPermission.as_view().__name__)

    def test_permission_experiment_resolves(self):
        """
        Test that all permission urls for experiments resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/permission/test/col1/exp1/')
        self.assertEqual(match.func.__name__, ResourceUserPermission.as_view().__name__)

    def test_permission_channel_layer_resolves(self):
        """
        Test that all permission urls for channel or layers resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/permission/test/col1/exp1/ch1/')
        self.assertEqual(match.func.__name__, ResourceUserPermission.as_view().__name__)

class BossCoreGroupRoutingTests(APITestCase):

    def test_group_resolves(self):
        """
        Test that all group urls resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/group/test/')
        self.assertEqual(match.func.__name__, BossGroup.as_view().__name__)

    def test_group_member_resolves(self):
        """
        Test that all group_member urls for experiments resolves correctly

        Returns: None

        """

        match = resolve('/' + version + '/group-member/test/testuser/')
        self.assertEqual(match.func.__name__, BossGroupMember.as_view().__name__)

        match = resolve('/' + version + '/group-member/test/')
        self.assertEqual(match.func.__name__, BossGroupMember.as_view().__name__)

