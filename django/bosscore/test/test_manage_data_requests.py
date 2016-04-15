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
from django.http import HttpRequest
from rest_framework.request import Request

from ..request import BossRequest
from ..models import *
from django.conf import settings
version  = settings.BOSS_VERSION
from .setup_db import setupTestDB


class ManageDataRequestTests(APITestCase):
    """
    Class to test bossrequest
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        setupTestDB.insert_test_data()


    def test_request_collection(self):
        """
        Test initialization of cutout requests for the datamodel
        :return:
        """
        url = '/' + version + '/manage-data/col1/'
        expectedValue = 'col1'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version

        ret = BossRequest(drfrequest)


