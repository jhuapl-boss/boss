from django.conf import settings
from django.http import HttpRequest

from rest_framework.test import APITestCase
from rest_framework.request import Request

from bosscore.request import BossRequest

from spdb.project import BossResourceDjango

from .setup_db import SetupTestDB


version = settings.BOSS_VERSION


class TestDjangoResource(APITestCase):

    def setUp(self):
        """Setup test by inserting data model items into the database"""
        SetupTestDB.insert_test_data()

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

        self.request_layer = BossRequest(drfrequest)

    def test_basic_resource_col(self):
        """Test basic get collection interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        col = resource.get_collection()

        assert col.name == self.request_channel.collection.name
        assert col.description == self.request_channel.collection.description

    def test_basic_resource_coord_frame(self):
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

    def test_basic_resource_experiment(self):
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

    def test_basic_resource_channel_no_time(self):
        """Test basic get channel interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        assert resource.is_channel() == True

        assert not resource.get_layer()

        channel = resource.get_channel()

        assert channel.name == self.request_channel.channel_layer.name
        assert channel.description == self.request_channel.channel_layer.description
        assert channel.datatype == self.request_channel.channel_layer.datatype

    def test_basic_resource_layer_no_time(self):
        """Test basic get layer interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_layer)

        assert resource.is_channel() == False

        assert not resource.get_channel()

        layer = resource.get_layer()
        assert layer.name == self.request_layer.channel_layer.name
        assert layer.description == self.request_layer.channel_layer.description
        assert layer.datatype == self.request_layer.channel_layer.datatype
        assert layer.base_resolution == self.request_layer.channel_layer.base_resolution
        assert layer.parent_channels == self.request_layer.channel_layer.linked_channel_layers

#def test_basic_resource_time_samples(self):
#    """Test basic get and set time samples interface

#    Returns:
#        None

#    """
#    setup_data = self.get_image_dict()
#    resource = BossResourceBasic(setup_data)

#    assert resource.is_channel() == True

#    assert resource.get_time_samples() == [0]

#    resource.set_time_samples([0, 1, 2, 3, 4, 5])
#    assert resource.get_time_samples() == [0, 1, 2, 3, 4, 5]

#    resource.set_time_samples(3)
#    assert resource.get_time_samples() == [3]

    def test_basic_resource_get_boss_key(self):
        """Test basic get boss key interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        assert resource.get_boss_key() == self.request_channel.get_boss_key()
        assert resource.get_boss_key() == ['col1&exp1&channel1&0']

    def test_basic_resource_get_lookup_key(self):
        """Test basic get lookup key interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        assert resource.get_lookup_key() == self.request_channel.get_lookup_key()

    def test_basic_resource_get_data_type(self):
        """Test basic get datatype interface

        Returns:
            None

        """
        resource = BossResourceDjango(self.request_channel)

        assert resource.get_data_type() == self.request_channel.channel_layer.datatype
        assert resource.get_data_type() == self.request_channel.channel_layer.datatype
