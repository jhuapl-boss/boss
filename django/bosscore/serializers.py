from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User
from guardian.shortcuts import get_objects_for_user

class UserSerializer(serializers.ModelSerializer):
    collections = serializers.PrimaryKeyRelatedField(many=True, queryset=Collection.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'collections')


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
    linked_channel_layers = NameOnlySerializer(many=True, read_only=True)
    is_channel = serializers.BooleanField(default=True, read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = ChannelLayer
        fields = ('name', 'description', 'experiment', 'is_channel', 'default_time_step',
                  'datatype', 'linked_channel_layers','creator')


class LayerSerializer(serializers.ModelSerializer):
    linked_channel_layers = NameOnlySerializer(many=True, read_only=True)
    is_channel = serializers.BooleanField(default=False, read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = ChannelLayer
        fields = ('name', 'description', 'is_channel', 'experiment', 'default_time_step',
                  'datatype', 'linked_channel_layers', 'creator')


class ChannelLayerSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = ChannelLayer
        fields = ('name', 'description', 'experiment', 'is_channel', 'default_time_step', 'datatype',
                  'linked_channel_layers', 'creator')


class ExperimentSerializer(serializers.ModelSerializer):

    channel_layers = ChannelLayerSerializer(many=True, read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')

    def get_fields(self):
        fields = super(ExperimentSerializer, self).get_fields()
        if 'request' in self.context:
            collections = get_objects_for_user(self.context['view'].request.user, 'add_collection', klass=Collection)
            fields['collection'].queryset = collections
        return fields


    class Meta:
        model = Experiment
        fields = ('name', 'description', 'collection', 'coord_frame', 'num_hierarchy_levels', 'hierarchy_method',
                  'max_time_sample', 'channel_layers', 'creator')


class CollectionSerializer(serializers.ModelSerializer):

    experiments = ExperimentSerializer(many=True, read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')


    class Meta:
        model = Collection
        fields = ('name', 'description', 'experiments', 'creator')
        depth=1


class BossLookupSerializer(serializers.ModelSerializer):

    class Meta:
        model = BossLookup
        fields = ('lookup_key', 'boss_key', 'collection_name', 'experiment_name', 'channel_layer_name')