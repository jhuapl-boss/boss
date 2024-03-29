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
from django.urls import resolve
from django.conf import settings
from bossmeta.views import BossMeta

version = settings.BOSS_VERSION


class BossCoreMetaServiceRoutingTests(APITestCase):

    def test_meta_urls_resolves_to_BossMeta_views(self):
        """
        Test to make sure the meta URL for get, post, delete and update with all
        datamodel params resolves to the meta view

        Returns: None
        """
        match = resolve('/' + version + '/meta/col1/')
        self.assertEqual(match.func.__name__, BossMeta.as_view().__name__)

        match = resolve('/' + version + '/meta/col1/exp1/')
        self.assertEqual(match.func.__name__, BossMeta.as_view().__name__)

        match = resolve('/' + version + '/meta/col1/exp1/ch1/')
        self.assertEqual(match.func.__name__, BossMeta.as_view().__name__)
