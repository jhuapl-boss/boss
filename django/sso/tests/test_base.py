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
import sys

def patch_check_role():
    # DP NOTE: has to be called after (potentially) mocking bossutils, but
    #          before importing any of the sso code

    # After the checks for bossutils, as it will import bosscore

    def fake_check_role(role):
        def check_role_decorator(func):
            @wraps(func)
            def wrapped(self, *args, **kwargs):
                # Just pass through for the fake.
                return func(self, *args, **kwargs)

            return wrapped
        return check_role_decorator

    mock.patch('bosscore.privileges.check_role', fake_check_role).start() # apply right now

# If bossutils is not currently installed, stubb out the library
try:
    import bossutils

    patch_check_role()

    from sso.views.views_user import KeyCloakError
except ImportError:
    # Stubb out
    sys.modules['bossutils'] = mock.MagicMock()
    sys.modules['bossutils.aws'] = mock.MagicMock()
    sys.modules['bossutils.logger'] = mock.MagicMock()
    sys.modules['bossutils.keycloak'] = mock.MagicMock()

    patch_check_role()

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

class TestBase(APITestCase):
    def setUp(self):
        """
        Initialize the database
        :return:
        """
        self.user = User.objects.create_user(username=TEST_USER)

    def makeRequest(self, get=None, post=None, delete=None, data=None):
        factory = APIRequestFactory()

        prefix = '/' + VERSION

        if get is not None:
            request = factory.get(prefix + get)
        elif post is not None:
            request = factory.post(prefix + post, data)
        elif delete is not None:
            request = factory.delete(prefix + delete)
        else:
            raise Exception('Unsupported request type')

        force_authenticate(request, user=self.user)

        return request
