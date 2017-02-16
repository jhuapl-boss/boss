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
from bossingest.views import IngestJobView, IngestJobStatusView, IngestJobListView

version = settings.BOSS_VERSION


class BossIngestServiceRoutingTests(APITestCase):

    def test_ingest_urls_resolves_to_BossIngest_views(self):
        """
        Test that the ingest url resolves to the ingest service view

        Returns: None
        """
        match = resolve('/' + version + '/ingest/')
        self.assertEqual(match.func.__name__, IngestJobView.as_view().__name__)

    def test_ingest_urls_with_id_resolves_to_BossIngest_views(self):
        """
        Test that the ingest url resolves to the ingest service view

        Returns: None
        """
        match = resolve('/' + version + '/ingest/1')
        self.assertEqual(match.func.__name__, IngestJobView.as_view().__name__)

    def test_ingest_urls_with_id_status_resolves_to_BossIngestStatus_views(self):
        """
        Test that the ingest status  url resolves to the ingest status view

        Returns: None
        """
        match = resolve('/' + version + '/ingest/1/status')
        self.assertEqual(match.func.__name__, IngestJobStatusView.as_view().__name__)


