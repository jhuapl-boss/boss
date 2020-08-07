# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory
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


from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.conf import settings
from mgmt.views import PUBLIC_ACCESS_USERNAME

version = settings.BOSS_VERSION

class TestMgmtView(APITestCase):
    def test_public_access_user_token_protected(self):
        """Do not allow change of the public-access token."""
        publicuser = User.objects.create_user(username=PUBLIC_ACCESS_USERNAME)
        self.client.force_login(publicuser)
        self.client.force_authenticate(user=publicuser)

        url = f'/{version}/mgmt/token/'
        actual = self.client.post(url)

        self.assertEqual(403, actual.status_code)
