from django.core.urlresolvers import resolve
from .views import CutoutView, Cutout

from bosscore.test.setup_db import setupTestDB

from rest_framework import status
from rest_framework.test import APITestCase

import blosc
import numpy as np
from django.conf import settings

version = settings.BOSS_VERSION


class CutoutInterfaceRoutingTests(APITestCase):

    def setUp(self):
        """
        Initialize the database
        :return:
        """

        setupTestDB.insert_test_data()


    def test_full_token_cutout_resolves_to_cutout(self):
        """
        Test to make sure the cutout URL with all datamodel params resolves
        :return:
        """
        view_based_cutout = resolve('/' + version + '/cutout/col1/exp1/ds1/2/0:5/0:6/0:2')
        self.assertEqual(view_based_cutout.func.__name__, Cutout.as_view().__name__)

    def test_view_token_cutout_resolves_to_cutoutview(self):
        """
        Test to make sure the cutout URL with just a view token resolves
        :return:
        """
        view_based_cutout = resolve('/' + version + '/cutout/2/0:5/0:6/0:2?view=token1')
        self.assertEqual(view_based_cutout.func.__name__, CutoutView.as_view().__name__)


class CutoutInterfaceViewTests(APITestCase):
    # TODO: Add proper view tests once cache is integrated, currently just making sure you get the right statuscode back

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        setupTestDB.insert_test_data()

    def test_full_token_cutout_post(self):
        """
        Test to make sure posting a block of data returns a 201
        :return:
        """
        a = np.random.randint(0, 100, (5, 6, 2))
        h = a.tobytes()
        bb = blosc.compress(h, typesize=8)

        response = self.client.post('/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2', bb,
                                    content_type='application/octet-stream')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_view_token_cutout_post(self):
        """
        Test to make sure posting a block of data returns a 201
        :return:
        """
        a = np.random.randint(0, 100, (5, 6, 2))
        h = a.tobytes()
        bb = blosc.compress(h, typesize=8)

        response = self.client.post('/' + version + '/cutout/2/0:5/0:6/0:2?view=token1', bb,
                                    content_type='application/octet-stream')

        # TODO: Once views are implemented need to finish test and switch to 200
        #self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_full_token_cutout_get(self):
        """
        Test to make sure getting a block of data returns a 200
        :return:
        """
        response = self.client.get('/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2',
                                   content_type='application/octet-stream')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_token_cutout_get(self):
        """
        Test to make sure getting a block of data returns a 200
        :return:
        """
        response = self.client.get('/' + version + '/cutout/2/0:5/0:6/0:2?view=token1',
                                   content_type='application/octet-stream')

        # TODO: Once views are implemented need to finish test and switch to 200
        #self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_token_cutout_get_missing_token_error(self):
        """
        Test to make sure you get an error
        :return:
        """
        response = self.client.get('/' + version + '/cutout/2/0:5/0:6/0:2',
                                   content_type='application/octet-stream')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
