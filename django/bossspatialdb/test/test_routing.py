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

from django.core.urlresolvers import resolve
from ..views import Cutout

from rest_framework.test import APITestCase

from django.conf import settings

version = settings.BOSS_VERSION


class CutoutInterfaceRoutingTests(APITestCase):
    """Test that Cutout interface endpoints route properly"""

    def setUp(self):
        """
        Initialize the database
        :return:
        """

    def test_full_token_cutout_resolves_to_cutout(self):
        """
        Test to make sure the cutout URL with all datamodel params resolves
        :return:
        """
        view_based_cutout = resolve('/' + version + '/cutout/col1/exp1/ds1/2/0:5/0:6/0:2')
        self.assertEqual(view_based_cutout.func.__name__, Cutout.as_view().__name__)

    def test_full_token_cutout_resolves_to_cutout_time(self):
        """
        Test to make sure the cutout URL with all datamodel params resolves
        :return:
        """
        view_based_cutout = resolve('/' + version + '/cutout/col1/exp1/ds1/2/0:5/0:6/0:2/5:57')
        self.assertEqual(view_based_cutout.func.__name__, Cutout.as_view().__name__)

