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
from django.contrib.auth.models import User, Group
from guardian.shortcuts import get_objects_for_user
from .models import Collection, Experiment, Channel, CoordinateFrame, BossLookup, BossRole


class CoordinateFrameSerializer(serializers.ModelSerializer):
    """
    Coordinate frame serializer
    """

    class Meta:
        model = CoordinateFrame
        fields = ('name', 'description', 'x_start', 'x_stop', 'y_start', 'y_stop', 'z_start', 'z_stop',
                  'x_voxel_size', 'y_voxel_size', 'z_voxel_size', 'voxel_unit', 'time_step', 'time_step_unit')


class CoordinateFrameUpdateSerializer(serializers.ModelSerializer):
    """
    Coordinate frame update serializer
    """

    class Meta:
        model = CoordinateFrame
        fields = ('name', 'description')

    def is_valid(self, raise_exception=False):
        super().is_valid(False)

        fields_keys = set(self.fields.keys())
        input_keys = set(self.initial_data.keys())

        additional_fields = input_keys - fields_keys

        if bool(additional_fields):
            self._errors['fields'] = ['Cannot update the following readonly fields:{}.'.format(list(additional_fields))]

        if self._errors and raise_exception:
            raise serializers.ValidationError(self.errors)

        return not bool(self._errors)


class ChannelSerializer(serializers.ModelSerializer):
    """
    Channel serializers
    """
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Channel
        fields = ('name', 'description', 'experiment', 'default_time_step', 'type',
                  'base_resolution', 'datatype', 'creator')


class ChannelUpdateSerializer(serializers.ModelSerializer):
    """
    Channel update serializer
    """

    class Meta:
        model = Channel
        fields = ('name', 'description', 'default_time_step', 'base_resolution')

    def is_valid(self, raise_exception=False):
        super().is_valid(False)

        fields_keys = set(self.fields.keys())
        input_keys = set(self.initial_data.keys())

        additional_fields = input_keys - fields_keys

        if bool(additional_fields):
            self._errors['fields'] = ['Cannot update the following readonly fields:{}.'.format(list(additional_fields))]

        if self._errors and raise_exception:
            raise serializers.ValidationError(self.errors)

        return not bool(self._errors)

class ChannelReadSerializer(serializers.ModelSerializer):
    """
    Channel serializer for GETS
    """
    creator = serializers.ReadOnlyField(source='creator.username')
    experiment = serializers.ReadOnlyField(source='experiment.name')
    sources = serializers.SerializerMethodField()
    related = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ('name', 'description', 'experiment', 'default_time_step', 'type',
                  'base_resolution', 'datatype', 'creator', 'sources', 'related')

    def get_sources(self, channel):
        source_names = channel.sources.values_list('name', flat=True)
        list_sources = [name for name in source_names ]
        return list_sources

    def get_related(self, channel):
        related_names = channel.related.values_list('name', flat=True)
        list_related = [name for name in related_names ]
        return list_related




class ExperimentSerializer(serializers.ModelSerializer):
    """
        Experiment serializer used for POST's
    """
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
                  'max_time_sample', 'creator')


class ExperimentUpdateSerializer(serializers.ModelSerializer):
    """
    Experiment update serializer
    """

    class Meta:
        model = Experiment
        fields = ('name', 'description', 'num_hierarchy_levels', 'hierarchy_method', 'max_time_sample')

    def is_valid(self, raise_exception=False):
        super().is_valid(False)

        fields_keys = set(self.fields.keys())
        input_keys = set(self.initial_data.keys())

        additional_fields = input_keys - fields_keys

        if bool(additional_fields):
            self._errors['fields'] = ['Cannot update the following readonly fields:{}.'.format(list(additional_fields))]

        if self._errors and raise_exception:
            raise serializers.ValidationError(self.errors)

        return not bool(self._errors)


class ExperimentReadSerializer(serializers.ModelSerializer):
    """
    Experiment Serializer used for GETS
    """
    channels = serializers.SerializerMethodField()
    creator = serializers.ReadOnlyField(source='creator.username')
    collection = serializers.ReadOnlyField(source='collection.name')
    coord_frame = serializers.ReadOnlyField(source='coord_frame.name')

    class Meta:
        model = Experiment
        fields = ('channels', 'name', 'description', 'collection', 'coord_frame', 'num_hierarchy_levels',
                  'hierarchy_method', 'max_time_sample', 'creator')

    def get_channels(self, experiment):
        return experiment.channels.values_list('name', flat=True)


class CollectionSerializer(serializers.ModelSerializer):
    """
    Collection serializer
    """
    experiments = serializers.SerializerMethodField()
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Collection
        fields = ('name', 'description', 'experiments', 'creator')

    def get_experiments(self, collection):
        return collection.experiments.values_list('name', flat=True)


class BossLookupSerializer(serializers.ModelSerializer):

    class Meta:
        model = BossLookup
        fields = ('lookup_key', 'boss_key', 'collection_name', 'experiment_name', 'channel_name')


class BossRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = BossRole
        fields = ('user', 'role')


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('name',)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
