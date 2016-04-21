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

from ..models import *
from django.contrib.auth.models import User


class setupTestDB:
    def __init__(self):
        self.user = None

    def create_user(self):
        self.user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        return self.user

    def create_super_user(self):
        self.user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        return self.user

    def get_user(self):
        return self.user

    def set_user(self, user):
        self.user = user

    def insert_test_data(self):
        max_time = 10
        col = Collection.objects.create(name='col1', creator=self.user)
        lkup_key = str(col.pk)
        bs_key = col.name
        BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key, collection_name=col.name)


        cf = CoordinateFrame.objects.create(name='cf1', description='cf1',
                                            x_start=0, x_stop=1000,
                                            y_start=0, y_stop=1000,
                                            z_start=0, z_stop=1000,
                                            x_voxel_size=4, y_voxel_size=4, z_voxel_size=4,
                                            time_step=1, creator=self.user
                                            )
        exp = Experiment.objects.create(name='exp1', collection=col, coord_frame=cf, num_hierarchy_levels=10,
                                        max_time_sample=max_time, creator=self.user)
        lkup_key = str(col.pk) + '&' + str(exp.pk)
        bs_key = col.name + '&' + str(exp.name)
        BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key, collection_name=col.name,
                                  experiment_name=exp.name)

        channel = ChannelLayer.objects.create(name='channel1', experiment=exp, is_channel=True,
                                              default_time_step=0, base_resolution=0, datatype='uint8', creator=self.user)
        base_lkup_key = str(col.pk) + '&' + str(exp.pk) + '&' + str(channel.pk)
        base_bs_key = col.name + '&' + exp.name + '&' + channel.name
        BossLookup.objects.create(lookup_key=base_lkup_key, boss_key=base_bs_key,
                                  collection_name=col.name,
                                  experiment_name=exp.name,
                                  channel_layer_name=channel.name
                                  )
        for time in range(0, max_time + 1):
            lkup_key = base_lkup_key + '&' + str(time)
            bs_key = base_bs_key + '&' + str(time)
            BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key,
                                      collection_name=col.name,
                                      experiment_name=exp.name,
                                      channel_layer_name=channel.name
                                      )

        layer = ChannelLayer.objects.create(name='layer1', experiment=exp, is_channel=False,
                                            default_time_step=0, creator=self.user, base_resolution=0, datatype='uint8')
        base_lkup_key = str(col.pk) + '&' + str(exp.pk) + '&' + str(layer.pk)
        base_bs_key = col.name + '&' + exp.name + '&' + layer.name
        BossLookup.objects.create(lookup_key=base_lkup_key, boss_key=base_bs_key,
                                  collection_name=col.name,
                                  experiment_name=exp.name,
                                  channel_layer_name=channel.name
                                  )
        for time in range(0, max_time + 1):
            lkup_key = base_lkup_key + '&' + str(time)
            bs_key = base_bs_key + '&' + str(time)
            BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key,
                                      collection_name=col.name,
                                      experiment_name=exp.name,
                                      channel_layer_name=layer.name
                                      )

    def insert_additional_objects(self):
        max_time = 10
        col = Collection.objects.create(name='col66', creator=self.user)
        lkup_key = str(col.pk)
        bs_key = col.name
        BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key, collection_name=col.name)

        cf = CoordinateFrame.objects.create(name='cf2', description='cf2',
                                            x_start=0, x_stop=1000,
                                            y_start=0, y_stop=1000,
                                            z_start=0, z_stop=1000,
                                            x_voxel_size=4, y_voxel_size=4, z_voxel_size=4,
                                            time_step=1, creator=self.user
                                            )
        exp = Experiment.objects.create(name='exp66', collection=col, coord_frame=cf, num_hierarchy_levels=10,
                                        max_time_sample=max_time, creator=self.user)
        lkup_key = str(col.pk) + '&' + str(exp.pk)
        bs_key = col.name + '&' + str(exp.name)
        BossLookup.objects.create(lookup_key=lkup_key, boss_key=bs_key, collection_name=col.name,
                                  experiment_name=exp.name)



