# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import force_authenticate
from rest_framework import status

from django.conf import settings

from bosscore.test.setup_db import DjangoSetupLayer
from bossobject.views import Reserve

version = settings.BOSS_VERSION


class TestReserveIDView(APITestCase):
    layer = DjangoSetupLayer

    def setUp(self):
        """ Copy params from the Layer setUpClass
        """
        # Setup config
        self.kvio_config = self.layer.kvio_config
        self.state_config = self.layer.state_config
        self.object_store_config = self.layer.object_store_config
        self.user = self.layer.user

        # Log Django User in
        self.client.force_login(self.user)

    def test_reserve_ids_view(self):
        """A test to reserve ids"""

        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/reserve/col1/exp1/layer1/10')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Reserve.as_view()(request, collection='col1', experiment='exp1', channel='layer1', num_ids='10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['start_id'], 1)
        self.assertEqual(response.data['count'], '10')
