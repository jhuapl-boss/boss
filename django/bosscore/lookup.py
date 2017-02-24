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

import re
from .serializers import BossLookupSerializer
from .models import BossLookup
from .error import BossError, ErrorCodes


class LookUpKey:
    """
    Bosskey manager

    """
    @staticmethod
    def add_lookup(lookup_key, boss_key, collection_name, experiment_name=None,
                   channel_name=None):
        """
        Add the lookup key that correspond to a data model object
        Args:
            lookup_key: Lookup key for the object that was created
            boss_key: Bosskey for the objec that we created
            collection_name: Collection name . Matches the collection in the bosskey
            experiment_name: Experiment name . Matches the experiment in the bosskey
            channel_name: Channel name . Matches the channel in the bosskey

        Returns: None

        """
        # Create the boss lookup key

        lookup_data = {'lookup_key': lookup_key, 'boss_key': boss_key,
                       'collection_name': collection_name,
                       'experiment_name': experiment_name,
                       'channel_name': channel_name
                       }
        serializer = BossLookupSerializer(data=lookup_data)
        if serializer.is_valid():
            serializer.save()

    @staticmethod
    def get_lookup_key(bkey):
        """
        Get the lookup keys for a request
        Args:
            bkey: Bosskey that corresponds to a request

        Returns:
            Lookup key

        """
        lookup_obj = BossLookup.objects.get(boss_key=bkey)
        return lookup_obj

    @staticmethod
    def delete_lookup_key(collection, experiment=None, channel=None):
        """
        Delete a lookupkey for a specific bosskey

        Args:
            collection: Collection Name
            experiment : Experiment Name
            channel : Channel name
        Returns:
            None

        """

        try:
            if channel and experiment and collection:
                lookup_obj = BossLookup.objects.get(collection_name=collection, experiment_name=experiment,
                                                    channel_name=channel)
                lookup_obj.delete()
            elif experiment and collection:
                lookup_obj = BossLookup.objects.get(collection_name=collection, experiment_name=experiment)
                lookup_obj.delete()
            elif collection:
                lookup_obj = BossLookup.objects.get(collection_name=collection)
                lookup_obj.delete()
            else:
                raise BossError(404, "Cannot delete lookupkey", 30000)

        except BossLookup.DoesNotExist:
            raise BossError(404, "Cannot find a lookup key for bosskey", 30000)

    @staticmethod
    def update_lookup(lookup_key, boss_key, collection_name, experiment_name=None, channel_name=None):
        """
        Update the fields that correspond to a lookupkey
        Args:
            lookup_key: Lookup key for the object that was created
            boss_key: Bosskey for the objec that we created
            collection_name: Collection name . Matches the collection in the bosskey
            experiment_name: Experiment name . Matches the experiment in the bosskey
            channel_name: Channel name . Matches the channel in the bosskey


        Returns: None

        """
        # Create the boss lookup key
        lookup_data = {'lookup_key': lookup_key, 'boss_key': boss_key,
                       'collection_name': collection_name,
                       'experiment_name': experiment_name,
                       'channel_name': channel_name
                       }
        lookup_obj = BossLookup.objects.get(lookup_key=lookup_key)
        serializer = BossLookupSerializer(lookup_obj, data=lookup_data, partial=True)

        if serializer.is_valid():
            serializer.save()

    @staticmethod
    def update_lookup_collection(lookup_key, boss_key, collection_name):
        """
        Update the fields that correspond to a lookupkey
        Args:
            lookup_key: Lookup key for the object that was created
            boss_key: Bosskey for the objec that we created
            collection_name: Collection name . Matches the collection in the bosskey

        Returns: None

        """
        try:
            # Create the boss lookup key
            lookup_data = {'lookup_key': lookup_key, 'boss_key': boss_key,
                           'collection_name': collection_name,
                           }
            lookup_obj = BossLookup.objects.get(lookup_key=lookup_key)
            old_collection_name = lookup_obj.collection_name
            serializer = BossLookupSerializer(lookup_obj, data=lookup_data, partial=True)

            if serializer.is_valid():
                serializer.save()
            else:
                raise BossError("{}. Error updating the collection name in the lookup key"
                                .format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)

            # update all object that reference this collection
            all_lookup_objs = BossLookup.objects.filter(collection_name=old_collection_name)\
                .exclude(lookup_key=lookup_key)
            for item in all_lookup_objs:
                split_key = item.boss_key.split('&')
                split_key[0] = collection_name
                boss_key = '&'.join(split_key)

                lookup_data = {'lookup_key': item.lookup_key, 'boss_key': boss_key,
                               'collection_name': collection_name
                               }
                serializer = BossLookupSerializer(item, data=lookup_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    raise BossError("{}. Error updating the collection name in the lookup key".
                                    format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)
        except BossLookup.DoesNotExist:
            raise BossError("Cannot update the lookup key", ErrorCodes.UNABLE_TO_VALIDATE)

    @staticmethod
    def update_lookup_experiment(lookup_key, boss_key, collection_name, experiment_name):
        """
        Update the fields that correspond to a lookupkey
        Args:
            lookup_key: Lookup key for the object that was created
            boss_key: Bosskey for the objec that we created
            collection_name: Collection name . Matches the collection in the bosskey
            experiment_name: Collection name . Matches the collection in the bosskey

        Returns: None

        """
        try:
            # Create the boss lookup key
            lookup_data = {'lookup_key': lookup_key, 'boss_key': boss_key, 'collection_name': collection_name,
                           'experiment_name': experiment_name,
                           }
            lookup_obj = BossLookup.objects.get(lookup_key=lookup_key)
            old_experiment_name = lookup_obj.experiment_name
            serializer = BossLookupSerializer(lookup_obj, data=lookup_data, partial=True)

            if serializer.is_valid():
                serializer.save()
            else:
                raise BossError("{}. Error updating the collection name in the lookup key".format(serializer.errors),
                                ErrorCodes.INVALID_POST_ARGUMENT)


            # update all channels that reference this experiment
            all_lookup_objs = BossLookup.objects.filter(experiment_name=old_experiment_name).exclude(
                lookup_key=lookup_key)
            for item in all_lookup_objs:

                split_key = item.boss_key.split('&')
                split_key[1] = experiment_name
                boss_key = '&'.join(split_key)

                boss_key = re.sub(old_experiment_name, experiment_name, item.boss_key)
                lookup_data = {'lookup_key': item.lookup_key, 'boss_key': boss_key,
                               'experiment_name': experiment_name
                               }
                serializer = BossLookupSerializer(item, data=lookup_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    raise BossError("{}. Error updating the collection name in the lookup key".
                                    format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)
        except BossLookup.DoesNotExist:
            raise BossError("Cannot update the lookup key", ErrorCodes.UNABLE_TO_VALIDATE)
