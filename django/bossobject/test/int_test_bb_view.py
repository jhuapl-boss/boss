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

from django.conf import settings
from rest_framework.test import APITestCase

from bossobject.test.bounding_box_view import BoundingBoxMixin
from bosscore.test.setup_db import DjangoSetupLayer

import redis


class BoundingBoxViewIntegrationTests(BoundingBoxMixin, APITestCase):
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

        # Flush cache between tests
        client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
