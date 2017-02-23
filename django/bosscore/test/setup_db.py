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

from ..models import Collection, Experiment, CoordinateFrame, Channel, BossLookup, BossRole, BossGroup

test_user = 'testuser'
test_group = 'testuser-primary'


class SetupTestDB:
    def __init__(self):
        self.user = self.create_super_user()

    def create_user(self, username=None):
        if not username:
            username = test_user

        self.user = User.objects.create_user(username=username, email=username+'@test.com', password=username)
        user_primary_group, created = Group.objects.get_or_create(name=username + '-primary')

        # add the user to the public group and primary group
        public_group, created = Group.objects.get_or_create(name='bosspublic')
        self.user.groups.add(user_primary_group)
        public_group.user_set.add(self.user)
        return self.user

    def add_role(self, role_name, user=None):
        if user is None:
            user = self.user
        BossRole.objects.create(user=user, role=role_name)

    def create_super_user(self):
        self.user = User.objects.create_superuser(username='bossadmin', email='bossadmin@theboss.io',
                                                  password='bossadmin')
        user_primary_group, created = Group.objects.get_or_create(name='bossadmin' + '-primary')

        # add the user to the public group and primary group and admin group
        public_group, created = Group.objects.get_or_create(name='bosspublic')
        admin_group, created = Group.objects.get_or_create(name='admin')
        self.user.groups.add(user_primary_group)
        self.user.groups.add(public_group)
        self.user.groups.add(admin_group)

        return self.user

    def get_user(self):
        return self.user

    def set_user(self, user):
        self.user = user

    def create_group(self, group_name):
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            self.user.groups.add(group)
            bgrp, created = BossGroup.objects.get_or_create(group=group, creator=self.user)

            # Assign permission to the users primary group
            group_name = self.user.username + "-primary"
            user_primary_group = Group.objects.get(name=group_name)
            assign_perm('maintain_group', user_primary_group, bgrp)
        return created

    def insert_test_data(self):

        self.add_collection('col1', 'Description for collection1')
        self.add_collection('col1-22', 'Description for collection1')
        self.add_collection('col2', 'Description for collection2')
        self.add_coordinate_frame('cf1', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4)
        self.add_experiment('col1', 'exp1', 'cf1', 10, 10, 1)
        self.add_experiment('col1', 'exp22', 'cf1', 10, 500, 1)
        self.add_channel('col1', 'exp1', 'channel1', 0, 0, 'uint8', 'image')
        self.add_channel('col1', 'exp1', 'channel2', 0, 0, 'uint8', 'image')
        self.add_channel('col1', 'exp1', 'channel3', 0, 0, 'uint64', 'annotation')
        self.add_channel('col1', 'exp1', 'layer1', 0, 0, 'uint64', 'annotation')

    def insert_spatialdb_test_data(self):

        self.add_collection('col1', 'Description for collection1')
        self.add_coordinate_frame('cf1', 'Description for cf1', 0, 100000, 0, 100000, 0, 100000, 4, 4, 4)
        self.add_experiment('col1', 'exp1', 'cf1', 10, 500, 1)
        self.add_channel('col1', 'exp1', 'channel1', 0, 0, 'uint8', 'image')
        self.add_channel('col1', 'exp1', 'channel2', 0, 0, 'uint16', 'image')
        self.add_channel('col1', 'exp1', 'layer1', 0, 0, 'uint64', 'annotation')

    def insert_ingest_test_data(self):

        self.add_collection('my_col_1', 'Description for collection1')
        self.add_coordinate_frame('cf1', 'Description for cf1', 0, 100000, 0, 100000, 0, 100000, 4, 4, 4)
        self.add_experiment('my_col_1', 'my_exp_1', 'cf1', 10, 500, 1)
        self.add_channel('my_col_1', 'my_exp_1', 'my_ch_1', 0, 0, 'uint8', 'image')

    @staticmethod
    def add_permissions(group, obj):
        # Get the type of model
        ct = ContentType.objects.get_for_model(obj)
        user_primary_group, created = Group.objects.get_or_create(name=group)

        assign_perm('read', user_primary_group, obj)
        assign_perm('add', user_primary_group, obj)
        assign_perm('update', user_primary_group, obj)
        assign_perm('delete', user_primary_group, obj)
        assign_perm('assign_group', user_primary_group, obj)
        assign_perm('remove_group', user_primary_group, obj)
        if ct.model == 'channel':
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
                             x_voxel_size, y_voxel_size, z_voxel_size):
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

        Returns:
            Coordinate Frame

        """
        cf = CoordinateFrame.objects.create(name=coordinate_frame, description=description,
                                            x_start=x_start, x_stop=x_stop, y_start=y_start, y_stop=y_stop,
                                            z_start=z_start, z_stop=z_stop,
                                            x_voxel_size=x_voxel_size, y_voxel_size=y_voxel_size,
                                            z_voxel_size=z_voxel_size, creator=self.user)
        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, cf)

        return cf

    def add_experiment(self, collection_name, experiment_name, coordinate_name, num_hierarchy_levels,
                       num_time_samples,time_step):
        """

        Args:
            collection_name: Name of the collection
            experiment_name: Name of the experiment
            coordinate_name: Name of the coordinate frame
            num_hierarchy_levels:
            num_time_samples:

        Returns:
            experiment

        """
        col = Collection.objects.get(name=collection_name)
        cf = CoordinateFrame.objects.get(name=coordinate_name)
        exp = Experiment.objects.create(name=experiment_name, collection=col, coord_frame=cf,
                                        num_hierarchy_levels=num_hierarchy_levels,
                                        num_time_samples=num_time_samples, time_step=time_step, creator=self.user)

        lkup_key = str(col.pk) + '&' + str(exp.pk)
        bs_key = col.name + '&' + str(exp.name)
        BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key, collection_name=col.name,
                                  experiment_name=exp.name)

        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, exp)

        return exp

    def add_channel(self, collection_name, experiment_name, channel_name,
                    default_time_sample, base_resolution, datatype, channel_type=None):
        """

        Args:
            collection_name: Name of the collection
            experiment_name: Name of the experiment
            channel_name: Name of the channel
            default_time_sample: Default time sample
            base_resolution: Base resolution of the channel
            datatype: Data type
            channel_type:  Channel Type (image or annotation)

        Returns:
            Channel

        """
        if channel_type is None:
            channel_type = 'image'
        col = Collection.objects.get(name=collection_name)
        exp = Experiment.objects.get(name=experiment_name, collection=col)
        channel = Channel.objects.create(name=channel_name, experiment=exp,
                                         default_time_sample=default_time_sample, base_resolution=base_resolution,
                                         type=channel_type, datatype=datatype, creator=self.user)

        base_lkup_key = str(col.pk) + '&' + str(exp.pk) + '&' + str(channel.pk)
        base_bs_key = col.name + '&' + exp.name + '&' + channel.name
        BossLookup.objects.create(lookup_key=base_lkup_key, boss_key=base_bs_key,
                                  collection_name=col.name,
                                  experiment_name=exp.name,
                                  channel_name=channel.name
                                  )

        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, channel)

        return channel
