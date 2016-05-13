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


from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm

from ..models import Collection, Experiment, CoordinateFrame, ChannelLayer, ChannelLayerMap, BossLookup

test_user = 'testuser'
test_group = 'testuser-primary'


class SetupTestDB:
    def __init__(self):
        self.user = None

    def create_user(self, username=None):
        if not username:
            username = test_user

        self.user = User.objects.create_user(username=username, email=username+'@test.com', password=username)
        user_primary_group, created = Group.objects.get_or_create(name=username + '-primary')

        self.user.groups.add(user_primary_group)
        return self.user

    def create_super_user(self):
        self.user = User.objects.create_superuser(username=test_user, email='test@test.com', password='testuser')
        return self.user

    def get_user(self):
        return self.user

    def set_user(self, user):
        self.user = user

    def create_group(self,group_name):
        group,created = Group.objects.get_or_create(name=group_name)
        return created

    def insert_test_data(self):

        self.add_collection('col1', 'Description for collection1')
        self.add_coordinate_frame('cf1', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4, 1)
        self.add_experiment('col1', 'exp1', 'cf1', 10, 10)
        self.add_channel('col1', 'exp1', 'channel1', 0, 0, 'uint8')
        self.add_channel('col1', 'exp1', 'channel2', 0, 0, 'uint8')
        self.add_layer('col1', 'exp1', 'layer1', 0, 0, 'uint16')
        self.add_channel_layer_map('col1', 'exp1', 'channel1', 'layer1')

    def add_permissions(self, group, obj):
        # Get the type of model
        ct = ContentType.objects.get_for_model(obj)
        user_primary_group, created = Group.objects.get_or_create(name=group)

        assign_perm('read', user_primary_group, obj)
        assign_perm('add', user_primary_group, obj)
        assign_perm('update', user_primary_group, obj)
        assign_perm('delete', user_primary_group, obj)
        assign_perm('assign_group', user_primary_group, obj)
        assign_perm('remove_group', user_primary_group, obj)
        if ct.model == 'channellayer':
            assign_perm('add_volumetric_data', user_primary_group, obj)
            assign_perm('read_volumetric_data', user_primary_group, obj)
            assign_perm('delete_volumetric_data', user_primary_group, obj)

    def add_collection(self, collection_name, description):
        """
        Add a new collection and lookupkey to the database
        Args:
            collection_name: Name of collection
            description: Description of the collection

        Returns:
            Collection

        """
        col = Collection.objects.create(name=collection_name, description=description, creator=self.user)

        # Add a lookup key
        lkup_key = str(col.pk)
        bs_key = col.name
        BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key, collection_name=col.name)

        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, col)

        return col

    def add_coordinate_frame(self, coordinate_frame, description, x_start, x_stop, y_start, y_stop, z_start, z_stop,
                             x_voxel_size, y_voxel_size, z_voxel_size, time_step):
        """
         Add a new coordinate frame
        Args:
            coordinate_frame: Name of the coordinate frame
            description: Description of the coordinate frame
            x_start:
            x_stop:
            y_start:
            y_stop:
            z_start:
            z_stop:
            x_voxel_size:
            y_voxel_size:
            z_voxel_size:
            time_step:

        Returns:
            Coordinate Frame

        """
        cf = CoordinateFrame.objects.create(name=coordinate_frame, description=description,
                                            x_start=x_start, x_stop=x_stop, y_start=y_start, y_stop=y_stop,
                                            z_start=z_start, z_stop=z_stop,
                                            x_voxel_size=x_voxel_size, y_voxel_size=y_voxel_size,
                                            z_voxel_size=z_voxel_size, time_step=time_step, creator=self.user)
        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, cf)

        return cf

    def add_experiment(self, collection_name, experiment_name, coordinate_name, num_hierarchy_levels, max_time_sample):
        """

        Args:
            collection_name: Name of the collection
            experiment_name: Name of the experiment
            coordinate_name: Name of the coordinate frame
            num_hierarchy_levels:
            max_time_sample:

        Returns:
            experiment

        """
        col = Collection.objects.get(name=collection_name)
        cf = CoordinateFrame.objects.get(name=coordinate_name)
        exp = Experiment.objects.create(name=experiment_name, collection=col, coord_frame=cf,
                                        num_hierarchy_levels=num_hierarchy_levels,
                                        max_time_sample=max_time_sample, creator=self.user)

        lkup_key = str(col.pk) + '&' + str(exp.pk)
        bs_key = col.name + '&' + str(exp.name)
        BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key, collection_name=col.name,
                                  experiment_name=exp.name)

        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, exp)

        return exp

    def add_channel(self, collection_name, experiment_name, channel_name, default_time_step, base_resolution, datatype):
        """

        Args:
            collection_name:
            experiment_name:
            channel_name:
            default_time_step:
            base_resolution:
            datatype:

        Returns:
            Channel

        """
        col = Collection.objects.get(name=collection_name)
        exp = Experiment.objects.get(name=experiment_name, collection=col)
        channel = ChannelLayer.objects.create(name=channel_name, experiment=exp, is_channel=True,
                                              default_time_step=default_time_step, base_resolution=base_resolution,
                                              datatype=datatype, creator=self.user)

        base_lkup_key = str(col.pk) + '&' + str(exp.pk) + '&' + str(channel.pk)
        base_bs_key = col.name + '&' + exp.name + '&' + channel.name
        BossLookup.objects.create(lookup_key=base_lkup_key, boss_key=base_bs_key,
                                  collection_name=col.name,
                                  experiment_name=exp.name,
                                  channel_layer_name=channel.name
                                  )

        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, channel)

        return channel

    def add_layer(self, collection_name, experiment_name, layer_name, default_time_step, base_resolution, datatype):
        """

        Args:
            collection_name:
            experiment_name:
            layer_name:
            default_time_step:
            base_resolution:
            datatype:

        Returns:
            Layer

        """
        col = Collection.objects.get(name=collection_name)
        exp = Experiment.objects.get(name=experiment_name, collection=col)
        layer = ChannelLayer.objects.create(name=layer_name, experiment=exp, is_channel=False,
                                            default_time_step=default_time_step, base_resolution=base_resolution,
                                            datatype=datatype, creator=self.user)

        base_lkup_key = str(col.pk) + '&' + str(exp.pk) + '&' + str(layer.pk)
        base_bs_key = col.name + '&' + exp.name + '&' + layer.name
        BossLookup.objects.create(lookup_key=base_lkup_key, boss_key=base_bs_key,
                                  collection_name=col.name,
                                  experiment_name=exp.name,
                                  channel_layer_name=layer.name
                                  )
        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, layer)

        return layer

    def add_channel_layer_map(self, collection_name, experiment_name, channel_name, layer_name):
        """

        Args:
            collection_name:
            experiment_name:
            channel_name:
            layer_name:

        Returns:

        """
        col = Collection.objects.get(name=collection_name)
        exp = Experiment.objects.get(name=experiment_name, collection=col)
        ch = ChannelLayer.objects.get(name=channel_name, experiment=exp)
        layer = ChannelLayer.objects.get(name=layer_name, experiment=exp)
        ChannelLayerMap.objects.create(channel=ch, layer=layer)
