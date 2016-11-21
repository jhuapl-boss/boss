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

from bossobject.views import Reserve, Ids, BoundingBox

version = version = settings.BOSS_VERSION


class ReserveIDRoutingTests(APITestCase):

    def test_reserve_id_resolves(self):
        """
        Test that the reserve id url resolves

        Returns: None

        """
        match = resolve('/' + version + '/reserve/col1/exp1/channel1/10')
        self.assertEqual(match.func.__name__, Reserve.as_view().__name__)

class IdsRoutingTests(APITestCase):

    def test_ids_resolves(self):
        """
        Test that the ids url resolves

        Returns: None

        """
        match = resolve('/' + version + '/ids/col1/exp1/channel1/2/0:5/0:6/0:2')
        self.assertEqual(match.func.__name__, Ids.as_view().__name__)

        #ids url with time
        match = resolve('/' + version + '/ids/col1/exp1/channel1/2/0:5/0:6/0:2/0:1')
        self.assertEqual(match.func.__name__, Ids.as_view().__name__)

class BoundingBoxRoutingTests(APITestCase):

    def test_reserve_id_resolves(self):
        """
        Test that the bounding box urls resolve

        Returns: None

        """
        match = resolve('/' + version + '/boundingbox/col1/exp1/channel1/0/10')
        self.assertEqual(match.func.__name__, BoundingBox.as_view().__name__)
