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
from django.http import HttpRequest

from rest_framework.test import APITestCase
from rest_framework.request import Request

from bosscore.request import BossRequest

from spdb.project import BossResourceDjango

from bosscore.test.setup_db import SetupTestDB


version = settings.BOSS_VERSION


class TestDjangoResource(APITestCase):

    def setUp(self):
        """Setup test by inserting data model items into the database"""
        dbsetup = SetupTestDB()
        user = dbsetup.create_user()
        dbsetup.add_role("resource-manager", user)
        self.client.force_login(user)
        dbsetup.insert_test_data()

        url = '/' + version + '/collection/col1/experiment/exp1/channel/channel33/'
        data = {'description': 'This is a new channel', 'type': 'annotation', 'datatype': 'uint8',
                'source': ['channel1'],
                'related': ['channel2', 'channel3']}
        response = self.client.post(url, data=data)

        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'
        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version

        self.request_channel = BossRequest(drfrequest)

        # Setup Layer
        url = '/' + version + '/cutout/col1/exp1/layer1/2/0:5/0:6/0:2/'
        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version

        self.request_annotation = BossRequest(drfrequest)

        url = '/' + version + '/cutout/col1/exp1/channel33/2/0:5/0:6/0:2/'
        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version

        self.request_channel_links = BossRequest(drfrequest)

    def test_django_resource_col(self):
        """Test basic get collection interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        col = resource.get_collection()

        assert col.name == self.request_channel.collection.name
        assert col.description == self.request_channel.collection.description

    def test_django_resource_coord_frame(self):
        """Test basic get coordinate frame interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        coord = resource.get_coord_frame()

        assert coord.name == self.request_channel.coord_frame.name
        assert coord.description == self.request_channel.coord_frame.description
        assert coord.x_start == self.request_channel.coord_frame.x_start
        assert coord.x_stop == self.request_channel.coord_frame.x_stop
        assert coord.y_start == self.request_channel.coord_frame.y_start
        assert coord.y_stop == self.request_channel.coord_frame.y_stop
        assert coord.z_start == self.request_channel.coord_frame.z_start
        assert coord.z_stop == self.request_channel.coord_frame.z_stop
        assert coord.x_voxel_size == self.request_channel.coord_frame.x_voxel_size
        assert coord.y_voxel_size == self.request_channel.coord_frame.y_voxel_size
        assert coord.z_voxel_size == self.request_channel.coord_frame.z_voxel_size
        assert coord.voxel_unit == self.request_channel.coord_frame.voxel_unit
        assert coord.time_step == self.request_channel.coord_frame.time_step
        assert coord.time_step_unit == self.request_channel.coord_frame.time_step_unit

    def test_django_resource_experiment(self):
        """Test basic get experiment interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        exp = resource.get_experiment()

        assert exp.name == self.request_channel.experiment.name
        assert exp.description == self.request_channel.experiment.description
        assert exp.num_hierarchy_levels == self.request_channel.experiment.num_hierarchy_levels
        assert exp.hierarchy_method == self.request_channel.experiment.hierarchy_method

    def test_django_resource_channel_image(self):
        """Test basic get channel interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        channel = resource.get_channel()
        assert channel.is_image() is True

        assert channel.name == self.request_channel.channel.name
        assert channel.description == self.request_channel.channel.description
        assert channel.datatype == self.request_channel.channel.datatype
        assert channel.type == self.request_channel.channel.type
        assert channel.base_resolution == self.request_channel.channel.base_resolution
        assert channel.default_time_step == self.request_channel.channel.default_time_step
        assert channel.related == []
        assert channel.source == []

    def test_django_resource_channel_annotation(self):
        """Test basic get channel when an annotation interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_annotation)

        channel = resource.get_channel()
        assert channel.is_image() is False

        assert channel.name == self.request_annotation.channel.name
        assert channel.description == self.request_annotation.channel.description
        assert channel.datatype == self.request_annotation.channel.datatype
        assert channel.type == self.request_annotation.channel.type
        assert channel.base_resolution == self.request_annotation.channel.base_resolution
        assert channel.default_time_step == self.request_annotation.channel.default_time_step
        assert channel.related == []
        assert channel.source == []

    def test_django_resource_channel_image_with_links(self):
        """Test basic get channel interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel_links)

        channel = resource.get_channel()
        assert channel.is_image() is False

        assert channel.name == self.request_channel_links.channel.name
        assert channel.description == self.request_channel_links.channel.description
        assert channel.datatype == self.request_channel_links.channel.datatype
        assert channel.type == self.request_channel_links.channel.type
        assert channel.base_resolution == self.request_channel_links.channel.base_resolution
        assert channel.default_time_step == self.request_channel_links.channel.default_time_step
        assert channel.related == ['channel2', 'channel3']
        assert channel.source == ['channel1']

    def test_django_resource_get_boss_key(self):
        """Test basic get boss key interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        assert resource.get_boss_key() == self.request_channel.get_boss_key()
        assert resource.get_boss_key() == 'col1&exp1&channel1'

    def test_django_resource_get_lookup_key(self):
        """Test basic get lookup key interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        assert resource.get_lookup_key() == self.request_channel.get_lookup_key()
        assert isinstance(resource.get_lookup_key(), str)

    def test_django_resource_get_data_type(self):
        """Test basic get datatype interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)
        assert resource.get_data_type() == self.request_channel.channel.datatype

    def test_django_resource_to_dict_channel(self):
        """Test basic get to dict interface for images

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)
        data = resource.to_dict()
        assert "channel" in data
        assert "collection" in data
        assert "experiment" in data
        assert "lookup_key" in data
        assert "boss_key" in data
        assert "coord_frame" in data

    def test_django_resource_to_dict_annotation(self):
        """Test basic get to dict interface for annotations

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_annotation)
        data = resource.to_dict()
        assert "channel" in data
        assert "collection" in data
        assert "experiment" in data
        assert "lookup_key" in data
        assert "boss_key" in data
        assert "coord_frame" in data
