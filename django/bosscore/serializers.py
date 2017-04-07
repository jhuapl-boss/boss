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
from .models import Collection, Experiment, Channel, CoordinateFrame, BossLookup, BossRole, BossGroup


class CoordinateFrameSerializer(serializers.ModelSerializer):
    """
    Coordinate frame serializer
    """

    class Meta:
        model = CoordinateFrame
        fields = ('name', 'description', 'x_start', 'x_stop', 'y_start', 'y_stop', 'z_start', 'z_stop',
                  'x_voxel_size', 'y_voxel_size', 'z_voxel_size', 'voxel_unit')


class CoordinateFrameDeleteSerializer(serializers.ModelSerializer):
    """
    Coordinate frame serializer
    """
    exps = serializers.SerializerMethodField()
    class Meta:
        model = CoordinateFrame
        fields = ('name', 'description', 'x_start', 'x_stop', 'y_start', 'y_stop', 'z_start', 'z_stop',
                  'x_voxel_size', 'y_voxel_size', 'z_voxel_size', 'voxel_unit', 'exps')

    def get_exps(self, coord):
        return coord.exps.exclude(to_be_deleted__isnull=False).values_list('name', flat=True)

    def get_valid_exps(self,coord):
        "return all experiments that reference this coordframe that are not marked to be deleted"
        return coord.exps.exclude(to_be_deleted__isnull=False).values_list('name', flat=True)


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
        fields = ('name', 'description', 'experiment', 'default_time_sample', 'type',
                  'base_resolution', 'datatype', 'downsample_status', 'creator')

    def validate(self, data):
        """Validate the default_time_step and base_resolution

        If these are included,validate that they are within the bounds of num_time_samples and num_hierarchy_levels.
        Args:
            data (dict): The data fields to be validated.
        Returns:
            data (dict): The validated data fields.
        Raises:
            ValidationError: If values are out of range.
        """
        errors = {}

        # Get the experiment
        exp = data.get('experiment')
        num_time_samples = exp.num_time_samples
        num_hierarchy_levels = exp.num_hierarchy_levels

        default_time_sample = data.get('default_time_sample', None)
        base_resolution = data.get('base_resolution', None)

        # Validate that default_time_step is less than the num_time_samples
        if default_time_sample is not None and default_time_sample >= num_time_samples:
            errors['default_time_sample'] = 'Ensure this value is less that the experiments num_time_samples {}.'\
                .format(num_time_samples)

        # Validate that base_Resolution is less than the num_hierarchy_levels
        if base_resolution is not None and base_resolution >= num_hierarchy_levels:
            errors['base_resolution'] = 'Ensure this value is less that the experiments maximum number of ' \
                                        'hierarchy levels {}.'.format(num_hierarchy_levels)

        if len(errors):
            raise serializers.ValidationError(errors)

        return data


class ChannelUpdateSerializer(serializers.ModelSerializer):
    """
    Channel update serializer
    """

    class Meta:
        model = Channel
        fields = ('name', 'description', 'default_time_sample', 'base_resolution', 'sources', 'related')

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
        fields = ('name', 'description', 'experiment', 'default_time_sample', 'type',
                  'base_resolution', 'datatype', 'creator', 'sources', 'downsample_status', 'related')

    def get_sources(self, channel):
        """
        Returns a list of source channel names for a given channel
        Args:
            channel:

        Returns:
            List of source channel names
        """
        source_names = channel.sources.exclude(to_be_deleted__isnull=False).values_list('name', flat=True)
        list_sources = [name for name in source_names]
        return list_sources

    def get_related(self, channel):
        """
            Returns a list of related channel names for a given channel
            Args:
                channel:

            Returns:
                List of source related names
        """
        related_names = channel.related.exclude(to_be_deleted__isnull=False).values_list('name', flat=True)
        list_related = [name for name in related_names]
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
                  'num_time_samples', 'time_step', 'time_step_unit', 'creator')


class ExperimentUpdateSerializer(serializers.ModelSerializer):
    """
    Experiment update serializer
    """

    class Meta:
        model = Experiment
        fields = ('name', 'description', 'num_hierarchy_levels', 'hierarchy_method', 'num_time_samples',
                  'time_step', 'time_step_unit')

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
                  'hierarchy_method', 'num_time_samples', 'time_step', 'time_step_unit', 'creator')

    def get_channels(self, experiment):
        return experiment.channels.exclude(to_be_deleted__isnull=False).values_list('name', flat=True)

    def get_channels_permissions(self, collection, experiment, cur_user):
        "return all channels that are not marked to be deleted and the user has read permissions on"

        collection_obj = Collection.objects.get(name=collection)
        experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
        channels = get_objects_for_user(cur_user, 'read', klass=Channel).filter(experiment=experiment_obj)
        channels = channels.exclude(to_be_deleted__isnull=False).values_list('name', flat=True)
        return channels


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
        return collection.experiments.exclude(to_be_deleted__isnull=False).values_list('name', flat=True)

    def get_experiments_permissions(self, collection, cur_user):
        "return all experiments that are not marked to be deleted and that the user has read permissions on"
        collection_obj = Collection.objects.get(name=collection)
        all_experiments = get_objects_for_user(cur_user, 'read', klass=Experiment).exclude(to_be_deleted__isnull=False)
        return all_experiments.filter(collection=collection_obj).values_list('name', flat=True)


class BossLookupSerializer(serializers.ModelSerializer):

    class Meta:
        model = BossLookup
        fields = ('lookup_key', 'boss_key', 'collection_name', 'experiment_name', 'channel_name')


class BossRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = BossRole
        fields = ('user', 'role')


class BossGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = BossGroup
        fields = ('group', 'creator')


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('name',)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
