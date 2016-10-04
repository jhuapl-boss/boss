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

from django.core.urlresolvers import resolve
from bosstiles.views import Image, Tile

from rest_framework.test import APITestCase

from django.conf import settings

version = settings.BOSS_VERSION


class TileInterfaceRoutingTests(APITestCase):
    """Test that Cutout interface endpoints route properly"""

    def setUp(self):
        """
        Initialize the database
        :return:
        """

    def test_full_token_image_resolves(self):
        """
        Test to make sure the tiles URL with all datamodel params resolves
        :return:
        """
        view_tiles = resolve('/' + version + '/image/col1/exp1/ds1/xy/2/0:5/0:6/1')
        self.assertEqual(view_tiles.func.__name__, Image.as_view().__name__)

        view_tiles = resolve('/' + version + '/image/col1/exp1/ds1/xz/2/0:5/1/1:6')
        self.assertEqual(view_tiles.func.__name__, Image.as_view().__name__)

        view_tiles = resolve('/' + version + '/image/col1/exp1/ds1/yz/2/5/1:6/1:6')
        self.assertEqual(view_tiles.func.__name__, Image.as_view().__name__)

    def test_full_token_image_time_resolves(self):
        """
        Test to make sure the tiles URL with all datamodel params resolves
        :return:
        """
        view_tiles = resolve('/' + version + '/image/col1/exp1/ds1/xy/2/0:5/0:6/1/1')
        self.assertEqual(view_tiles.func.__name__, Image.as_view().__name__)

        view_tiles = resolve('/' + version + '/image/col1/exp1/ds1/xz/2/0:5/1/1:6/2')
        self.assertEqual(view_tiles.func.__name__, Image.as_view().__name__)

        view_tiles = resolve('/' + version + '/image/col1/exp1/ds1/yz/2/5/1:6/1:6/3/')
        self.assertEqual(view_tiles.func.__name__, Image.as_view().__name__)

    def test_full_token_tile_resolves(self):
        """
        Test to make sure the tiles URL with all datamodel params resolves
        :return:
        """
        view_tiles = resolve('/' + version + '/tile/col1/exp1/ds1/xy/512/2/0/1/1')
        self.assertEqual(view_tiles.func.__name__, Tile.as_view().__name__)

        view_tiles = resolve('/' + version + '/tile/col1/exp1/ds1/xy/512/2/0/1/1/')
        self.assertEqual(view_tiles.func.__name__, Tile.as_view().__name__)

        view_tiles = resolve('/' + version + '/tile/col1/exp1/ds1/xz/512/2/0/1/1')
        self.assertEqual(view_tiles.func.__name__, Tile.as_view().__name__)

        view_tiles = resolve('/' + version + '/tile/col1/exp1/ds1/yz/512/2/0/1/1')
        self.assertEqual(view_tiles.func.__name__, Tile.as_view().__name__)

    def test_full_token_tile_time_resolves(self):
        """
        Test to make sure the tiles URL with all datamodel params resolves
        :return:
        """
        view_tiles = resolve('/' + version + '/tile/col1/exp1/ds1/xy/512/2/0/1/1/3')
        self.assertEqual(view_tiles.func.__name__, Tile.as_view().__name__)

        view_tiles = resolve('/' + version + '/tile/col1/exp1/ds1/xz/512/2/0/1/1/3')
        self.assertEqual(view_tiles.func.__name__, Tile.as_view().__name__)

        view_tiles = resolve('/' + version + '/tile/col1/exp1/ds1/yz/512/2/0/1/1/3')
        self.assertEqual(view_tiles.func.__name__, Tile.as_view().__name__)
        view_tiles = resolve('/' + version + '/tile/col1/exp1/ds1/yz/512/2/0/1/1/3/')
        self.assertEqual(view_tiles.func.__name__, Tile.as_view().__name__)
