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

from rest_framework import serializers
from django.contrib.auth.models import User
from guardian.shortcuts import get_objects_for_user
from .models import Collection, Experiment, ChannelLayer, CoordinateFrame, ChannelLayerMap, BossLookup


class UserSerializer(serializers.ModelSerializer):
    collections = serializers.PrimaryKeyRelatedField(many=True, queryset=Collection.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'collections')


class CoordinateFrameSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='pk')

    class Meta:
        model = CoordinateFrame
        fields = ('id', 'name', 'description', 'x_start', 'x_stop', 'y_start', 'y_stop', 'z_start', 'z_stop',
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
    id = serializers.ReadOnlyField(source='pk')
    linked_channel_layers = NameOnlySerializer(many=True, read_only=True)
    is_channel = serializers.BooleanField(default=True, read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = ChannelLayer
        fields = ('id', 'name', 'description', 'experiment', 'is_channel', 'default_time_step',
                  'base_resolution', 'datatype', 'linked_channel_layers', 'creator')


class LayerSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='pk')
    linked_channel_layers = NameOnlySerializer(many=True, read_only=True)
    is_channel = serializers.BooleanField(default=False, read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = ChannelLayer
        fields = ('id', 'name', 'description', 'is_channel', 'experiment', 'default_time_step',
                  'base_resolution', 'datatype', 'linked_channel_layers', 'creator')


class ChannelLayerSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='pk')
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = ChannelLayer
        fields = ('id', 'name', 'description', 'experiment', 'is_channel', 'default_time_step', 'datatype',
                  'base_resolution', 'linked_channel_layers', 'creator')


class ExperimentSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='pk')
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
        fields = ('id', 'name', 'description', 'collection', 'coord_frame', 'num_hierarchy_levels', 'hierarchy_method',
                  'max_time_sample', 'channel_layers', 'creator')


class CollectionSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='pk')
    experiments = ExperimentSerializer(many=True, read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Collection
        fields = ('id', 'name', 'description', 'experiments', 'creator')
        depth = 1


class BossLookupSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='pk')

    class Meta:
        model = BossLookup
        fields = ('id', 'lookup_key', 'boss_key', 'collection_name', 'experiment_name', 'channel_layer_name')
