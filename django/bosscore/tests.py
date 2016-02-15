from rest_framework.test import APITestCase
from rest_framework import status
import json

from .error import BossHTTPError


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

