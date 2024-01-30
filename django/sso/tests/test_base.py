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

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from django.conf import settings
from functools import wraps
from unittest import mock
from bosscore.models import BossRole
import sys

# If bossutils is not currently installed, stub out the library
try:
    import bossutils

    from sso.views.views_user import KeyCloakError
except ImportError:
    # Stub out
    sys.modules['bossutils'] = mock.MagicMock()
    sys.modules['bossutils.aws'] = mock.MagicMock()
    sys.modules['bossutils.logger'] = mock.MagicMock()
    sys.modules['bossutils.keycloak'] = mock.MagicMock()

    class KeyCloakError(Exception):
        def __init__(self, status, data):
            super(KeyCloakError, self).__init__(data)
            self.status = status
            self.data = data

    # Override the Mock version of KeyCloakError with an actual exception type
    import sso.views.views_user
    sso.views.views_user.KeyCloakError = KeyCloakError

def raise_error(*args, **kwargs):
    raise KeyCloakError(500, {})

VERSION = settings.BOSS_VERSION
TEST_USER = 'testuser'
ADMIN_USER = 'adminuser'
USER_MANAGER_USER = 'usermgruser'

class TestBase(APITestCase):
    def setUp(self):
        """
        Initialize the database
        :return:
        """
        self.user = User.objects.create_user(username=TEST_USER)
        self.admin_user = User.objects.create_user(username=ADMIN_USER)
        BossRole.objects.create(role='admin', user=self.admin_user).save()
        self.user_mgr_user = User.objects.create_user(username=USER_MANAGER_USER)
        BossRole.objects.create(role='user-manager', user=self.user_mgr_user).save()

    def makeRequest(self, get=None, post=None, delete=None, data=None, user=None):
        factory = APIRequestFactory()

        if user is None:
            user = self.user

        prefix = '/' + VERSION

        if get is not None:
            request = factory.get(prefix + get)
        elif post is not None:
            request = factory.post(prefix + post, data)
        elif delete is not None:
            request = factory.delete(prefix + delete)
        else:
            raise Exception('Unsupported request type')

        force_authenticate(request, user=user)

        return request
