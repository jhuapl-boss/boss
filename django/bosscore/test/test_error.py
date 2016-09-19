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

import json
from rest_framework.test import APITestCase
from rest_framework import status

from ..error import BossHTTPError, BossError, BossParserError, ErrorCodes


class BossHTTPErrorTests(APITestCase):

    def test_bosshttperror(self):
        """
        test the boss http error
        :return:
        """
        response = BossHTTPError('UNIT TEST', 4000)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response_json = json.loads(response.content.decode('utf-8'))

        assert response_json['message'] == 'UNIT TEST'
        assert response_json['code'] == 4000
        assert response_json['status'] == 404


class TestBossError(APITestCase):
    def test_creation(self):
        with self.assertRaises(BossError):
            raise BossError("test", ErrorCodes.INVALID_URL)

    def test_params(self):
        try:
            raise BossError("test", ErrorCodes.INVALID_URL)
        except BossError as err:
            assert err.status_code == 400
            assert err.message == "test"
            assert err.error_code == 1000

    def test_to_http(self):
        try:
            raise BossError("test", 1000)
        except BossError as err:
            http_err = err.to_http()
            assert isinstance(http_err, BossHTTPError)


class TestBossParserError(APITestCase):
    def test_creation(self):
        err = BossParserError("test", ErrorCodes.INVALID_URL)
        assert err.status_code == 400
        assert err.message == "test"
        assert err.error_code == 1000

    def test_to_http(self):
        err = BossParserError("test", ErrorCodes.INVALID_URL)
        http_err = err.to_http()
        assert isinstance(http_err, BossHTTPError)

        self.assertEqual(http_err.status_code, status.HTTP_400_BAD_REQUEST)

        response_json = json.loads(http_err.content.decode('utf-8'))

        assert response_json['message'] == 'test'
        assert response_json['code'] == 1000
        assert response_json['status'] == 400

