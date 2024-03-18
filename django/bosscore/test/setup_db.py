# Copyright 2021 The Johns Hopkins University Applied Physics Laboratory
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
from ..views.views_resource import ChannelDetail
from ..constants import ADMIN_USER, ADMIN_GRP, PUBLIC_GRP
from ..permissions import BossPermissionManager

from spdb.spatialdb.test.setup import AWSSetupLayer


test_user = 'testuser'
test_group = 'testuser-primary'

# Used for testing proper handling of channel with non-zero base resolution.
BASE_RESOLUTION = 2
NUM_HIERARCHY_LEVELS = 7

# Experiment names used by insert_test_data().
EXP1 = 'exp1'
EXP22 = 'exp22'
EXP_BASE_RES = 'exp-base-res-test'
TEST_DATA_EXPERIMENTS = [EXP1, EXP22, EXP_BASE_RES]
EXP_NOT_PUBLIC = 'exp-not-public'

CHAN_BASE_RES = 'chan-with-base-res'
CHAN_NOT_PUBLIC = 'chan-not-public'

# Channel for cloudvolume tests uses this bucket name.
CLOUD_VOL_BUCKET = 'bossdb-test-data'
CVPATH_CHAN1 = 'col1/exp1/chan1'
CVPATH_CHAN2 = 'col1/exp1/chan2'
CVPATH_ANNO1 = 'col1/exp1/anno1'

# Collection names.
COLL_NOT_PUBLIC = 'col-not-public'

class SetupTestDB:
    def __init__(self, super_user=None):
        """
        Constructor.

        An existing super user may be supplied when creating an another
        instance of this class for additional test DB configuration.

        Args:
            super_user (Optional[User]): Provide an existing super user.
        """
        self.super_user = super_user
        self.user = super_user

    def create_user(self, username=None):
        # If you have yet to create the superuser, you need to do that first for permissions to work OK
        if self.super_user is None:
            self.create_super_user()

        if not username:
            username = test_user

        self.user = User.objects.create_user(username=username, email=username+'@test.com', password=username)
        user_primary_group, created = Group.objects.get_or_create(name=username + '-primary')

        # add the user to the public group and primary group
        public_group, created = Group.objects.get_or_create(name=PUBLIC_GRP)
        self.user.groups.add(user_primary_group)
        public_group.user_set.add(self.user)
        return self.user

    def add_role(self, role_name, user=None):
        if user is None:
            user = self.user
        BossRole.objects.create(user=user, role=role_name)

    def create_super_user(self, username=ADMIN_USER, email=None, password=ADMIN_USER):
        if self.super_user is not None:
            return

        if email is None:
            full_email = username + '@boss.io'
        else:
            full_email = email

        self.super_user = User.objects.create_superuser(username=username, email=full_email,
                                                        password=password)
        user_primary_group, created = Group.objects.get_or_create(name=ADMIN_USER+'-primary')

        # add the user to the public group and primary group and admin group
        public_group, created = Group.objects.get_or_create(name=PUBLIC_GRP)
        admin_group, created = Group.objects.get_or_create(name=ADMIN_GRP)
        self.super_user.groups.add(user_primary_group)
        self.super_user.groups.add(public_group)
        self.super_user.groups.add(admin_group)
        self.add_role('admin', self.super_user)

        # Keep this old behavior in case other code was relying on this side
        # effect.
        self.user = self.super_user

        return self.super_user

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
        self.add_collection('col1-22', 'Description for collection1-22')
        self.add_collection('col2', 'Description for collection2')
        self.add_collection(COLL_NOT_PUBLIC, 'Collection to test setting public', public=False)

        self.add_coordinate_frame('cf1', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4)
        
        self.add_experiment('col1', EXP1, 'cf1', 10, 500, 1)
        self.add_experiment('col1', EXP22, 'cf1', NUM_HIERARCHY_LEVELS, 10, 1)
        self.add_experiment('col1', EXP_BASE_RES, 'cf1', NUM_HIERARCHY_LEVELS, 10, 1)
        self.add_experiment(COLL_NOT_PUBLIC, EXP_NOT_PUBLIC, 'cf1', NUM_HIERARCHY_LEVELS, 1, 1, public=False)

        self.add_channel('col1', EXP1, 'channel1', 0, 0, 'uint8', 'image')
        self.add_channel('col1', EXP1, 'channel2', 0, 0, 'uint16', 'image')
        self.add_channel('col1', EXP1, 'channel3', 0, 0, 'uint64', 'annotation', ['channel1'])
        self.add_channel('col1', EXP_BASE_RES, CHAN_BASE_RES, 0, BASE_RESOLUTION, 'uint8', 'image')
        self.add_channel('col1', EXP1, 'layer1', 0, 0, 'uint64', 'annotation', ['channel1'])
        self.add_channel(COLL_NOT_PUBLIC, EXP_NOT_PUBLIC, CHAN_NOT_PUBLIC, 0, 0, 'uint8', 'image', public=False)

    def insert_lookup_test_data(self):
        """
        Test data for LookupTest test case.
        """

        self.add_collection('col1', 'Description for collection1')
        self.add_collection('col2', 'Description for collection2')

        self.add_coordinate_frame('cf1', 'Description for cf1', 0, 1000, 0, 1000, 0, 1000, 4, 4, 4)

        self.add_experiment('col1', 'exp1', 'cf1', 10, 10, 1)

        # This experiment is _purposed_ named the same as the exp in col1.
        # Ensuring that renaming an experiment does not affect experiments with
        # the same name in other collections.
        self.add_experiment('col2', 'exp1', 'cf1', 10, 500, 1)

        self.add_channel('col1', 'exp1', 'channel1', 0, 0, 'uint8', 'image')
        self.add_channel('col1', 'exp1', 'channel2', 0, 0, 'uint8', 'image')
        self.add_channel('col1', 'exp1', 'channel3', 0, 0, 'uint64', 'annotation', ['channel1'])
        self.add_channel('col1', 'exp1', 'layer1', 0, 0, 'uint64', 'annotation', ['channel1'])
        self.add_channel('col2', 'exp1', 'channel1', 0, 0, 'uinit8', 'image')

    def insert_spatialdb_test_data(self):

        self.add_collection('col1', 'Description for collection1')
        self.add_coordinate_frame('cf1', 'Description for cf1', 0, 100000, 0, 100000, 0, 100000, 4, 4, 4)
        self.add_experiment('col1', 'exp1', 'cf1', 10, 500, 1)
        self.add_channel('col1', 'exp1', 'channel1', 0, 0, 'uint8', 'image')
        self.add_channel('col1', 'exp1', 'channel2', 0, 0, 'uint16', 'image')
        self.add_channel('col1', 'exp1', 'layer1', 0, 0, 'uint64', 'annotation', ['channel1'])
        # bbchan1 is a channel for bounding box tests.
        self.add_channel('col1', 'exp1', 'bbchan1', 0, 0, 'uint64', 'annotation', ['channel1'])

    def insert_cloudvolume_test_data(self):
        """
        Test data for cloudvolume integration.
        """
        self.add_collection('col1-cvdb', 'Description for collection1')
        self.add_coordinate_frame('cf1-cvdb', 'Description for cf1', 0, 100000, 0, 100000, 0, 100000, 4, 4, 4)
        self.add_experiment('col1-cvdb', 'exp1', 'cf1-cvdb', 10, 500, 1)

        # Dev Note: Prepopulated cloudvolume layer for uint8 data located at this cloudpath
        self.add_channel('col1-cvdb', 'exp1', 'chan1', 0, 0, 'uint8', 'image',
                storage_type='cloudvol',
                bucket=CLOUD_VOL_BUCKET,
                cv_path=CVPATH_CHAN1)

        # Dev Note: Prepopulated cloudvolume layer for uint16 data located at this cloudpath
        self.add_channel('col1-cvdb', 'exp1', 'chan2', 0, 0, 'uint16', 'image',
                storage_type='cloudvol',
                bucket=CLOUD_VOL_BUCKET,
                cv_path=CVPATH_CHAN2)

        # Dev Note: Prepopulated cloudvolume layer for uint16 data located at this cloudpath
        self.add_channel('col1-cvdb', 'exp1', 'anno1', 0, 0, 'uint64', 'annotation',
                storage_type='cloudvol',
                bucket=CLOUD_VOL_BUCKET,
                cv_path=CVPATH_ANNO1)

    def insert_ingest_test_data(self):

        self.add_collection('my_col_1', 'Description for collection1')
        self.add_coordinate_frame('cf2-ingest', 'cf2-ingest', 0, 100000, 0, 100000, 0, 100000, 4, 4, 4)
        self.add_experiment('my_col_1', 'my_exp_1', 'cf2-ingest', 10, 500, 1)
        self.add_channel('my_col_1', 'my_exp_1', 'my_ch_1', 0, 0, 'uint8', 'image')

    def insert_iso_data(self):
        self.add_coordinate_frame('cf2aniso', 'Description for cf2', 0, 2000, 0, 5000, 0, 200, 4, 4, 35)
        self.add_experiment('col1', 'exp_aniso', 'cf2aniso', 8, 500, 1)
        self.add_channel('col1', 'exp_aniso', 'channel1', 0, 0, 'uint8', 'image')

        self.add_coordinate_frame('cf2iso', 'Description for cf2', 0, 2000, 0, 5000, 0, 200, 6, 6, 6)
        self.add_experiment('col1', 'exp_iso', 'cf2iso', 8, 500, 1, hierarchy_method="isotropic")
        self.add_channel('col1', 'exp_iso', 'channel1', 0, 0, 'uint8', 'image')

    def insert_downsample_data(self):
        """Some resources for small downsample tests

        Returns:
            (Tuple[Channel, Channel]): The channels created for the downsample test.
        """
        self.add_coordinate_frame('cf_ds_aniso', 'Description for cf2', 0, 4096, 0, 4096, 0, 128, 4, 4, 35)
        self.add_experiment('col1', 'exp_ds_aniso', 'cf_ds_aniso', 5, 500, 1)
        aniso_chan = self.add_channel('col1', 'exp_ds_aniso', 'channel1', 0, 0, 'uint8', 'image')

        self.add_coordinate_frame('cf_ds_iso', 'Description for cf2', 0, 4096, 0, 4096, 0, 128, 6, 6, 6)
        self.add_experiment('col1', 'exp_ds_iso', 'cf_ds_iso', 3, 500, 1, hierarchy_method="isotropic")
        iso_chan = self.add_channel('col1', 'exp_ds_iso', 'channel1', 0, 0, 'uint8', 'image')
        return (aniso_chan, iso_chan)

    def insert_downsample_write_data(self):
        """Some resources for writing to an off 0 base res (tests write at 4)"""
        self.add_experiment('col1', 'exp_ds_aniso_4', 'cf_ds_aniso', 5, 500, 1)
        self.add_channel('col1', 'exp_ds_aniso_4', 'channel1', 0, 4, 'uint8', 'image')

        self.add_experiment('col1', 'exp_ds_iso_4', 'cf_ds_iso', 5, 500, 1, hierarchy_method="isotropic")
        self.add_channel('col1', 'exp_ds_iso_4', 'channel1', 0, 4, 'uint8', 'image')


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

        if ct.model != 'coordinateframe':
            assign_perm('read_metadata', user_primary_group, obj)
            assign_perm('add_metadata', user_primary_group, obj)
            assign_perm('update_metadata', user_primary_group, obj)
            assign_perm('delete_metadata', user_primary_group, obj)

        if ct.model == 'channel':
            assign_perm('add_volumetric_data', user_primary_group, obj)
            assign_perm('read_volumetric_data', user_primary_group, obj)
            assign_perm('delete_volumetric_data', user_primary_group, obj)

        # Make sure admin group can also access.
        BossPermissionManager.add_permissions_admin_group(obj)

    def add_collection(self, collection_name, description, public=False):
        """
        Add a new collection and lookupkey to the database
        Args:
            collection_name: Name of collection
            description: Description of the collection
            public (bool): Is collection public?  Defaults to False.

        Returns:
            Collection

        """
        col, created = Collection.objects.get_or_create(name=collection_name, description=description, creator=self.user, public=public)

        # Add a lookup key
        lkup_key = str(col.pk)
        bs_key = col.name
        if created:
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
        cf, created = CoordinateFrame.objects.get_or_create(name=coordinate_frame, description=description,
                                            x_start=x_start, x_stop=x_stop, y_start=y_start, y_stop=y_stop,
                                            z_start=z_start, z_stop=z_stop,
                                            x_voxel_size=x_voxel_size, y_voxel_size=y_voxel_size,
                                            z_voxel_size=z_voxel_size, creator=self.user)
        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, cf)

        return cf

    def add_experiment(self, collection_name, experiment_name, coordinate_name, num_hierarchy_levels,
                       num_time_samples, time_step, hierarchy_method="anisotropic", public=False):
        """

        Args:
            collection_name: Name of the collection
            experiment_name: Name of the experiment
            coordinate_name: Name of the coordinate frame
            num_hierarchy_levels:
            num_time_samples:
            public (bool): Is experiment public?  Defaults to False.

        Returns:
            experiment

        """
        col = Collection.objects.get(name=collection_name)
        cf = CoordinateFrame.objects.get(name=coordinate_name)
        exp, created = Experiment.objects.get_or_create(name=experiment_name, collection=col, coord_frame=cf,
                                        num_hierarchy_levels=num_hierarchy_levels, hierarchy_method=hierarchy_method,
                                        num_time_samples=num_time_samples, time_step=time_step, creator=self.user,
                                        public=public)

        if created:
            lkup_key = str(col.pk) + '&' + str(exp.pk)
            bs_key = col.name + '&' + str(exp.name)
            BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key, collection_name=col.name,
                                    experiment_name=exp.name)

        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, exp)

        return exp

    def add_channel(self, collection_name, experiment_name, channel_name,
                    default_time_sample, base_resolution, datatype, 
                    channel_type=None, source_channels=[], public=False, storage_type='spdb', 
                    bucket=None, cv_path=None):
        """

        Args:
            collection_name (str): Name of the collection
            experiment_name (str): Name of the experiment
            channel_name (str): Name of the channel
            default_time_sample: Default time sample
            base_resolution: Base resolution of the channel
            datatype (str): Data type
            channel_type (str):  Channel Type (image or annotation)
            source_channels (list[str]): Source channel(s) for an annotation channel
            public (bool): Is channel public?  Defaults to False.
            storage_type (str): storage backend. default to spdb
            bucket (str | null): source bucket. if null defaults to cuboids bucket
            cv_path (str | null): cloudpath for cloudvolume data if backend is cloudvol. 

        Returns:
            Channel

        """
        if channel_type is None:
            channel_type = 'image'

        # Not setting up any related channels.
        related_channels = []

        col = Collection.objects.get(name=collection_name)
        exp = Experiment.objects.get(name=experiment_name, collection=col)
        channel, created = Channel.objects.get_or_create(name=channel_name, experiment=exp,
                                         default_time_sample=default_time_sample, base_resolution=base_resolution,
                                         type=channel_type, datatype=datatype, creator=self.user,
                                         public=public, storage_type=storage_type, bucket=bucket, cv_path=cv_path)

        src_chan_objs, rel_chan_objs = ChannelDetail.validate_source_related_channels(
                exp, source_channels, related_channels)

        # Add source channels.
        channel = ChannelDetail.add_source_related_channels(
                channel, exp, src_chan_objs, rel_chan_objs)

        # Set lookup key.
        base_lkup_key = str(col.pk) + '&' + str(exp.pk) + '&' + str(channel.pk)
        base_bs_key = col.name + '&' + exp.name + '&' + channel.name
        if created: 
            BossLookup.objects.create(lookup_key=base_lkup_key, boss_key=base_bs_key,
                                    collection_name=col.name,
                                    experiment_name=exp.name,
                                    channel_name=channel.name
                                    )

        # Give permissions to the users primary group
        primary_group = self.user.username + '-primary'
        self.add_permissions(primary_group, channel)

        return channel


class DjangoSetupLayer(AWSSetupLayer):
    """A nose2 layer for setting up temporary AWS resources for testing ONCE per run"""
    django_setup_helper = SetupTestDB()
    user = None

    @classmethod
    def setUp(cls):
        # Create a user in django
        cls.superuser = cls.django_setup_helper.create_super_user('django-superuser')
        cls.user = cls.django_setup_helper.create_user('django-testuser')
        cls.django_setup_helper.add_role('resource-manager')
        cls.django_setup_helper.set_user(cls.user)

        # Populate django models DB
        cls.django_setup_helper.insert_spatialdb_test_data()
        cls.django_setup_helper.insert_cloudvolume_test_data()