"""
Copyright 2016 The Johns Hopkins University Applied Physics Laboratory

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from rest_framework.test import APITestCase
from rest_framework import status
import json
import unittest

from ..error import BossHTTPError, BossError


class BossHTTPErrorTests(APITestCase):

    def test_bosshttperror(self):
        """
        test the boss http error
        :return:
        """
        response = BossHTTPError(404, 'UNIT TEST', 342634)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response_json = json.loads(response.content.decode('utf-8'))

        assert response_json['message'] == 'UNIT TEST'
        assert response_json['code'] == 342634
        assert response_json['status'] == 404

    def test_bosshttperror_no_code(self):
        """
        test the boss http error
        :return:
        """
        response = BossHTTPError(409, 'UNIT TEST')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        response_json = json.loads(response.content.decode('utf-8'))

        assert response_json['message'] == 'UNIT TEST'
        assert response_json['code'] == 0
        assert response_json['status'] == 409


class TestBossError(APITestCase):
    def test_creation(self):
        with self.assertRaises(BossError):
            raise BossError(404, "test", 10000)

    def test_params(self):
        try:
            raise BossError(404, "test", 10000)
        except BossError as err:
            assert err.args[0] == 404
            assert err.args[1] == "test"
            assert err.args[2] == 10000

    def test_to_http(self):
        try:
            raise BossError(404, "test", 10000)
        except BossError as err:
            http_err = err.to_http()
            assert isinstance(http_err, BossHTTPError)

