from rest_framework import serializers
from bosscore.models import *


class CoordinateFrameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoordinateFrame
        fields = ('name', 'description', 'x_start', 'x_stop', 'y_start', 'y_stop', 'z_start', 'z_stop',
                  'x_voxel_size', 'y_voxel_size', 'z_voxel_size', 'voxel_unit', 'time_step', 'time_step_unit')


class ChannelLayerSerializer(serializers.ModelSerializer):
    # Layers = TimeSampleSerializer(many=True, read_only=True)

    class Meta:
        model = ChannelLayer
        fields = ('name', 'description', 'experiment', 'is_channel', 'default_time_step', 'datatype', 'max_time_step', 'layer_map')


class ExperimentSerializer(serializers.ModelSerializer):
    channel_layers = ChannelLayerSerializer(many=True, read_only=True)

    class Meta:
        model = Experiment
        fields = ('name', 'description', 'collection', 'coord_frame', 'num_hierarchy_levels', 'hierarchy_method',
                  'channel_layers')


class CollectionSerializer(serializers.ModelSerializer):
    experiments = ExperimentSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = ('name', 'description', 'experiments')
