from rest_framework import serializers
from .models import *


class CoordinateFrameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoordinateFrame
        fields = ('name', 'description', 'x_start', 'x_stop', 'y_start', 'y_stop', 'z_start', 'z_stop',
                  'x_voxel_size', 'y_voxel_size', 'z_voxel_size', 'voxel_unit', 'time_step', 'time_step_unit')


class ChannelLayerMapSerializer(serializers.ModelSerializer):
    # Layers = TimeSampleSerializer(many=True, read_only=True)

    class Meta:
        model = ChannelLayerMap
        fields = ('channel', 'layer')

class NameOnlySerializer(serializers.ModelSerializer):

    class Meta:
        model = ChannelLayer
        fields = ('name',)

class ChannelSerializer(serializers.ModelSerializer):
    linked_channel_layers = NameOnlySerializer(many=True,read_only=True)
    is_channel = serializers.BooleanField(default=True,read_only=True)

    class Meta:
        model = ChannelLayer
        fields = ('name', 'description', 'experiment', 'is_channel', 'default_time_step', 'datatype','linked_channel_layers')

class LayerSerializer(serializers.ModelSerializer):
    linked_channel_layers = NameOnlySerializer(many=True, read_only=True)
    is_channel = serializers.BooleanField(default=False,read_only=True)
    class Meta:
        model = ChannelLayer
        fields = ('name', 'description', 'is_channel','experiment', 'default_time_step', 'datatype','linked_channel_layers')


class ChannelLayerSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChannelLayer
        fields = ('name', 'description', 'experiment', 'is_channel', 'default_time_step', 'datatype',
                  'linked_channel_layers')


class ExperimentSerializer(serializers.ModelSerializer):
    channel_layers = ChannelLayerSerializer(many=True, read_only=True)

    class Meta:
        model = Experiment
        fields = ('name', 'description', 'collection', 'coord_frame', 'num_hierarchy_levels', 'hierarchy_method',
                  'max_time_sample','channel_layers')


class CollectionSerializer(serializers.ModelSerializer):
    experiments = ExperimentSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = ('name', 'description', 'experiments')


class BossLookupSerializer(serializers.ModelSerializer):

    class Meta:
        model = BossLookup
        fields = ('lookup_key', 'boss_key', 'collection_name','experiment_name', 'channel_layer_name')