# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from bosscore.lookup import LookUpKey
from bosscore.models import Collection, Experiment, Channel
from bosscore.models import BossLookup
from rest_framework.test import APITestCase
from .setup_db import SetupTestDB
import unittest


class LookupTest(APITestCase):
    def setUp(self):
        dbsetup = SetupTestDB()
        user = dbsetup.create_user('testuser')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_lookup_test_data()

    def test_update_lookup_experiment(self):
        """
        On an experiment rename, make sure only resources that are children of
        the experiment are changed.

        This is a regression test.
        """
        new_exp_name = 'new_exp'
        collection = 'col2'
        orig_exp_name = 'exp1'

        collection_obj = Collection.objects.get(name=collection)
        experiment_obj = Experiment.objects.get(name=orig_exp_name, collection=collection_obj)
        lookup_key = str(collection_obj.pk) + '&' + str(experiment_obj.pk)
        boss_key = collection_obj.name + '&' + new_exp_name

        # Method under test.
        LookUpKey.update_lookup_experiment(
                lookup_key, boss_key, collection_obj.name, new_exp_name)

        # There should be still 5 rows in the lookup table with orig_exp_name
        # as the experiment name under col1.  There should be the experiment
        # and 4 channels.
        all_lookup_objs = BossLookup.objects.filter(experiment_name=orig_exp_name)
        self.assertEqual(5, len(all_lookup_objs))
