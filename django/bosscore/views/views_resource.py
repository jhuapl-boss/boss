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

from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from guardian.shortcuts import get_objects_for_user
from datetime import datetime
from functools import wraps

from bosscore.error import BossError, BossHTTPError, BossPermissionError, BossResourceNotFoundError, ErrorCodes
from bosscore.lookup import LookUpKey
from bosscore.permissions import BossPermissionManager
from bosscore.privileges import check_role

from bosscore.serializers import CollectionSerializer, ExperimentSerializer, ChannelSerializer, \
    CoordinateFrameSerializer, CoordinateFrameUpdateSerializer, ExperimentReadSerializer, ChannelReadSerializer, \
    ExperimentUpdateSerializer, ChannelUpdateSerializer, CoordinateFrameDeleteSerializer

from bosscore.models import Collection, Experiment, Channel, CoordinateFrame, Source


class CollectionDetail(APIView):

    """
    View to access a collection object

    """
    def get(self, request, collection):
        """
        Get a single instance of a collection

        Args:
            request: DRF Request object
            collection: Collection name specifying the collection you want
        Returns:
            Collection
        """
        try:
            collection_obj = Collection.objects.get(name=collection)

            # Check for permissions
            if request.user.has_perm("read", collection_obj):
                if collection_obj.to_be_deleted is not None:
                    return BossHTTPError("Invalid Request. This Resource has been marked for deletion",
                                         ErrorCodes.RESOURCE_MARKED_FOR_DELETION)

                serializer = CollectionSerializer(collection_obj)
                data = serializer.data
                data['experiments'] = serializer.get_experiments_permissions(collection_obj,request.user)
                return Response(data, status=200)
            else:
                return BossPermissionError('read', collection)
        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)

    @transaction.atomic
    @check_role("resource-manager")
    def post(self, request, collection):
        """Create a new collection

        View to create a new collection and an associated bosskey for that collection
        Args:
            request: DRF Request object
            collection : Collection name
        Returns:
            Collection

        """
        col_data = request.data.copy()
        col_data['name'] = collection

        # Save the object
        serializer = CollectionSerializer(data=col_data)
        if serializer.is_valid():
            serializer.save(creator=self.request.user)
            collection_obj = Collection.objects.get(name=col_data['name'])

            # Assign permissions to the users primary group and admin group
            BossPermissionManager.add_permissions_primary_group(self.request.user, collection_obj)
            BossPermissionManager.add_permissions_admin_group(collection_obj)

            lookup_key = str(collection_obj.pk)
            boss_key = collection_obj.name
            LookUpKey.add_lookup(lookup_key, boss_key, collection_obj.name)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return BossHTTPError("{}".format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)

    @transaction.atomic
    def put(self, request, collection):
        """
        Update a collection using django rest framework
        Args:
            request: DRF Request object
            collection: Collection name
        Returns:
            Collection
        """
        try:
            # Check if the object exists
            collection_obj = Collection.objects.get(name=collection)

            # Check for permissions
            if request.user.has_perm("update", collection_obj):
                serializer = CollectionSerializer(collection_obj, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()

                    # update the lookup key if you update the name
                    if 'name' in request.data and request.data['name'] != collection:
                        lookup_key = str(collection_obj.pk)
                        boss_key = request.data['name']
                        LookUpKey.update_lookup_collection(lookup_key, boss_key, request.data['name'])

                    return Response(serializer.data)
                else:
                    return BossHTTPError("{}".format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)
            else:
                return BossPermissionError('update', collection)
        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except BossError as err:
            return err.to_http()

    @transaction.atomic
    @check_role("resource-manager")
    def delete(self, request, collection):
        """
        Delete a collection
        Args:
            request: DRF Request object
            collection:  Name of collection to delete
        Returns:
            Http status
        """
        try:
            collection_obj = Collection.objects.get(name=collection)

            if request.user.has_perm("delete", collection_obj):

                # Are there experiments that reference it
                serializer = CollectionSerializer(collection_obj)
                if len(serializer.get_experiments(collection_obj)) > 0:
                    # This collection has experiments that reference it and cannot be deleted
                    return BossHTTPError("Collection {} has experiments that reference it and cannot be deleted."
                                         "Please delete the experiments first.".format(collection),
                                         ErrorCodes.INTEGRITY_ERROR)

                collection_obj.to_be_deleted = datetime.now()
                collection_obj.save()

                return HttpResponse(status=204)
            else:
                return BossPermissionError('delete', collection)
        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except ProtectedError:
            return BossHTTPError("Cannot delete {}. It has experiments that reference it.".format(collection),
                                 ErrorCodes.INTEGRITY_ERROR)


class CoordinateFrameDetail(APIView):
    """
    View to access a cordinate frame

    """
    def get(self, request, coordframe):
        """
        GET requests for a single instance of a coordinateframe
        Args:

            request: DRF Request object
            coordframe: Coordinate frame name specifying the coordinate frame you want
        Returns:
            CoordinateFrame
        """
        try:
            coordframe_obj = CoordinateFrame.objects.get(name=coordframe)
            if coordframe_obj.to_be_deleted is not None:
                return BossHTTPError("Invalid Request. This Resource has been marked for deletion",
                                     ErrorCodes.RESOURCE_MARKED_FOR_DELETION)
            serializer = CoordinateFrameSerializer(coordframe_obj)
            return Response(serializer.data)
        except CoordinateFrame.DoesNotExist:
            return BossResourceNotFoundError(coordframe)

    @transaction.atomic
    @check_role("resource-manager")
    def post(self, request, coordframe):
        """Create a new coordinate frame

        View to create a new coordinate frame
        Args:
            request: DRF Request object
            coordframe : Coordinate frame name
        Returns:
            CoordinateFrame

        """
        coordframe_data = request.data.copy()
        coordframe_data['name'] = coordframe

        serializer = CoordinateFrameSerializer(data=coordframe_data)
        if serializer.is_valid():
            serializer.save(creator=self.request.user)
            coordframe_obj = CoordinateFrame.objects.get(name=coordframe_data['name'])

            # Assign permissions to the users primary group and admin group
            BossPermissionManager.add_permissions_primary_group(self.request.user, coordframe_obj)
            BossPermissionManager.add_permissions_admin_group(coordframe_obj)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return BossHTTPError("{}".format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)

    @transaction.atomic
    def put(self, request, coordframe):
        """
        Update a coordinate frame using django rest framework

        Args:
            request: DRF Request object
            coordframe: Coordinate frame name
        Returns:
            CoordinateFrame
        """
        try:
            # Check if the object exists
            coordframe_obj = CoordinateFrame.objects.get(name=coordframe)

            if request.user.has_perm("update", coordframe_obj):
                serializer = CoordinateFrameUpdateSerializer(coordframe_obj, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()

                    # return the object back to the user
                    coordframe = serializer.data['name']
                    coordframe_obj = CoordinateFrame.objects.get(name=coordframe)
                    serializer = CoordinateFrameSerializer(coordframe_obj)
                    return Response(serializer.data)
                else:
                    return BossHTTPError("{}".format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)
            else:
                return BossPermissionError('update', coordframe)
        except CoordinateFrame.DoesNotExist:
            return BossResourceNotFoundError(coordframe)

    @transaction.atomic
    @check_role("resource-manager")
    def delete(self, request, coordframe):
        """
        Delete a coordinate frame
        Args:
            request: DRF Request object
            coordframe:  Name of coordinateframe to delete
        Returns:
            Http status
        """
        try:
            coordframe_obj = CoordinateFrame.objects.get(name=coordframe)

            if request.user.has_perm("delete", coordframe_obj):
                # Are there experiments that reference it
                serializer = CoordinateFrameDeleteSerializer(coordframe_obj)
                if len(serializer.get_valid_exps(coordframe_obj)) > 0:
                    # This collection has experiments that reference it and cannot be deleted
                    return BossHTTPError(" Coordinate frame {} has experiments that reference it and cannot be deleted."
                                         "Please delete the experiments first.".format(coordframe),
                                         ErrorCodes.INTEGRITY_ERROR)

                coordframe_obj.to_be_deleted = datetime.now()
                coordframe_obj.save()
                return HttpResponse(status=204)
            else:
                return BossPermissionError('delete', coordframe)
        except CoordinateFrame.DoesNotExist:
            return BossResourceNotFoundError(coordframe)
        except ProtectedError:
            return BossHTTPError("Cannot delete {}. It has experiments that reference it.".format(coordframe),
                                 ErrorCodes.INTEGRITY_ERROR)


class ExperimentDetail(APIView):
    """
    View to access an experiment

    """
    def get(self, request, collection, experiment):
        """
        GET requests for a single instance of a experiment

        Args:
            request: DRF Request object
            collection: Collection name specifying the collection you want
            experiment: Experiment name specifying the experiment instance
        Returns :
            Experiment
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            # Check for permissions
            if request.user.has_perm("read", experiment_obj):
                if experiment_obj.to_be_deleted is not None:
                    return BossHTTPError("Invalid Request. This Resource has been marked for deletion",
                                         ErrorCodes.RESOURCE_MARKED_FOR_DELETION)
                serializer = ExperimentReadSerializer(experiment_obj)
                data = serializer.data
                data['channels'] = serializer.get_channels_permissions(collection_obj,experiment_obj,request.user)
                return Response(data)
            else:
                return BossPermissionError('read', experiment)
        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except Experiment.DoesNotExist:
            return BossResourceNotFoundError(experiment)

    @transaction.atomic
    @check_role("resource-manager")
    def post(self, request, collection, experiment):
        """Create a new experiment

        View to create a new experiment and an associated bosskey for that experiment
        Args:
            request: DRF Request object
            collection : Collection name
            experiment : Experiment name
        Returns:
            Experiment

        """
        experiment_data = request.data.copy()
        experiment_data['name'] = experiment
        try:
            # Get the collection information
            collection_obj = Collection.objects.get(name=collection)

            if request.user.has_perm("add", collection_obj):
                experiment_data['collection'] = collection_obj.pk

                # Update the coordinate frame
                if 'coord_frame' not in experiment_data:
                    return BossHTTPError("This request requires a valid coordinate frame",
                                         ErrorCodes.INVALID_POST_ARGUMENT)

                coord_frame_obj = CoordinateFrame.objects.get(name=experiment_data['coord_frame'])
                experiment_data['coord_frame'] = coord_frame_obj.pk

                serializer = ExperimentSerializer(data=experiment_data)
                if serializer.is_valid():
                    serializer.save(creator=self.request.user)
                    experiment_obj = Experiment.objects.get(name=experiment_data['name'], collection=collection_obj)

                    # Assign permissions to the users primary group and admin group
                    BossPermissionManager.add_permissions_primary_group(self.request.user, experiment_obj)
                    BossPermissionManager.add_permissions_admin_group(experiment_obj)

                    lookup_key = str(collection_obj.pk) + '&' + str(experiment_obj.pk)
                    boss_key = collection_obj.name + '&' + experiment_obj.name
                    LookUpKey.add_lookup(lookup_key, boss_key, collection_obj.name, experiment_obj.name)

                    serializer = ExperimentReadSerializer(experiment_obj)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return BossHTTPError("{}".format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)
            else:
                return BossPermissionError('add', collection)
        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except CoordinateFrame.DoesNotExist:
            return BossResourceNotFoundError(experiment_data['coord_frame'])
        except ValueError:
            return BossHTTPError("Value Error.Collection id {} in post data needs to be an integer"
                                 .format(experiment_data['collection']), ErrorCodes.TYPE_ERROR)

    @transaction.atomic
    def put(self, request, collection, experiment):
        """
        Update a experiment using django rest framework

        Args:
            request: DRF Request object
            collection: Collection name
            experiment : Experiment name for the new experiment

        Returns:
            Experiment
        """
        try:
            # Check if the object exists
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            if request.user.has_perm("update", experiment_obj):
                serializer = ExperimentUpdateSerializer(experiment_obj, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()

                    # update the lookup key if you update the name
                    if 'name' in request.data and request.data['name'] != experiment:
                        lookup_key = str(collection_obj.pk) + '&' + str(experiment_obj.pk)
                        boss_key = collection_obj.name + '&' + request.data['name']
                        LookUpKey.update_lookup_experiment(lookup_key, boss_key, collection_obj.name, request.data['name'])

                    # return the object back to the user
                    experiment = serializer.data['name']
                    experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
                    serializer = ExperimentReadSerializer(experiment_obj)
                    return Response(serializer.data)
                else:
                    return BossHTTPError("{}".format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)
            else:
                return BossPermissionError('update', experiment)

        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except Experiment.DoesNotExist:
            return BossResourceNotFoundError(experiment)
        except BossError as err:
            return err.to_http()

    @transaction.atomic
    @check_role("resource-manager")
    def delete(self, request, collection, experiment):
        """
        Delete a experiment
        Args:
            request: DRF Request object
            collection:  Name of collection
            experiment: Experiment name to delete
        Returns:
            Http status
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            if request.user.has_perm("delete", experiment_obj):
                # Are there channels that reference it
                serializer = ExperimentReadSerializer(experiment_obj)
                if len(serializer.get_channels(experiment_obj)) > 0:
                    # This experiment has channels that reference it and cannot be deleted
                    return BossHTTPError(" Experiment {} has channels that reference it and cannot be deleted."
                                         "Please delete the channels first.".format(experiment),
                                         ErrorCodes.INTEGRITY_ERROR)

                experiment_obj.to_be_deleted = datetime.now()
                experiment_obj.save()

                return HttpResponse(status=204)
            else:
                return BossPermissionError('delete', experiment)
        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except Experiment.DoesNotExist:
            return BossResourceNotFoundError(experiment)
        except ProtectedError:
            return BossHTTPError("Cannot delete {}. It has channels that reference it."
                                 .format(experiment), ErrorCodes.INTEGRITY_ERROR)


class ChannelDetail(APIView):
    """
    View to access a channel

    """
    @staticmethod
    def validate_source_related_channels(experiment, source_channels, related_channels):
        """
        Validate that the list of source and related channels are channels that exist
        Args:
            experiment:
            source_channels:
            related_channels:

        Returns:

        """
        common = set(source_channels) & set(related_channels)
        if len(common) > 0:
            raise BossError("Related channels have to be different from source channels",
                            ErrorCodes.INVALID_POST_ARGUMENT)

        source_channel_obj = []
        related_channel_obj = []

        try:
            for name in source_channels:
                source_channel_obj.append(Channel.objects.get(name=name, experiment=experiment))

            for name in related_channels:
                related_channel_obj.append(Channel.objects.get(name=name, experiment=experiment))

            return (source_channel_obj,related_channel_obj)
        except Channel.DoesNotExist:
            raise BossError("Invalid channel names {} in the list of source/related channels channels ".format(name),
                            ErrorCodes.INVALID_POST_ARGUMENT)

    @staticmethod
    def add_source_related_channels(channel, experiment, source_channels, related_channels):
        """
        Add a list of source and related channels

        Args:
            related_channels:
            source_channels:
            experiment:
            channel:

        Returns:
            list : A list of channels id's if the list is valid

        """
        try:
            for source_channel in source_channels:
                channel.add_source(source_channel)

            for related_channel in related_channels:
                channel.related.add(related_channel.pk)

            channel.save()
            return channel
        except Exception as err:
            channel.delete()
            raise BossError("Exception adding source/related channels.{}".format(err), ErrorCodes.INVALID_POST_ARGUMENT)

    @staticmethod
    def update_source_related_channels(channel, experiment, source_channels, related_channels):
        """
        Update a list of source and related channels

        Args:
            related_channels: New list of related channels
            source_channels: New list of source channels
            experiment: Experiment for the current channel
            channel: Curren channel

        Returns:
            Updated Channel

        """
        try:
            # update ist of sources
            # Get all the source
            cur_sources = channel.sources.all()
            # Get the list of sources to remove
            rm_sources = [ch for ch in cur_sources if ch not in source_channels]
            for source in rm_sources:
                channel.remove_source(source)

            # add new sources
            add_sources = [ch for ch in source_channels if ch not in cur_sources]
            for source_channel in add_sources:
                channel.add_source(source_channel)

            cur_related = channel.related.all()
            rm_related = [ch for ch in cur_related if ch not in related_channels]
            for related in rm_related:
                channel.related.remove(related)

            add_related = [ch for ch in related_channels if ch not in cur_related]
            for related_channel in add_related:
                channel.related.add(related_channel.pk)

            channel.save()
            return channel
        except Exception as err:
            channel.delete()
            raise BossError("Exception adding source/related channels.{}".format(err), ErrorCodes.INVALID_POST_ARGUMENT)

    def get(self, request, collection, experiment, channel):
        """
        Retrieve information about a channel.
        Args:
            request: DRF Request object
            collection: Collection name
            experiment: Experiment name
            channel: Channel name

        Returns :
            Channel
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_obj = Channel.objects.get(name=channel, experiment=experiment_obj)

            # Check for permissions
            if request.user.has_perm("read", channel_obj):
                if channel_obj.to_be_deleted is not None:
                    return BossHTTPError("Invalid Request. This Resource has been marked for deletion",
                                         ErrorCodes.RESOURCE_MARKED_FOR_DELETION)
                serializer = ChannelReadSerializer(channel_obj)
                return Response(serializer.data)
            else:
                return BossPermissionError('read', channel)

        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except Experiment.DoesNotExist:
            return BossResourceNotFoundError(experiment)
        except Channel.DoesNotExist:
            return BossResourceNotFoundError(channel)
        except ValueError:
            return BossHTTPError("Value Error in post data", ErrorCodes.TYPE_ERROR)

    @transaction.atomic
    @check_role("resource-manager")
    def post(self, request, collection, experiment, channel):
        """
        Post a new Channel
        Args:
            request: DRF Request object
            collection: Collection name
            experiment: Experiment name
            channel: Channel name

        Returns :
            Channel
        """

        channel_data = request.data.copy()
        channel_data['name'] = channel

        try:
            # Get the collection and experiment
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)

            # Check for add permissions
            if request.user.has_perm("add", experiment_obj):
                channel_data['experiment'] = experiment_obj.pk

                # The source and related channels are names and need to be removed from the dict before serialization
                source_channels = channel_data.pop('sources', [])
                related_channels = channel_data.pop('related', [])

                # Source channels have to be included for new annotation channels
                if 'type' in channel_data and channel_data['type'] == 'annotation' and len(source_channels) == 0:
                    return BossHTTPError("Annotation channels require the source channel to be set. "
                                         "Specify a valid source channel in the post", ErrorCodes.INVALID_POST_ARGUMENT)

                # Validate the source and related channels if they are incuded
                channels = self.validate_source_related_channels(experiment_obj, source_channels, related_channels)
                source_channels_objs = channels[0]
                related_channels_objs = channels[1]

                # Validate and create the channel
                serializer = ChannelSerializer(data=channel_data)
                if serializer.is_valid():
                    serializer.save(creator=self.request.user)
                    channel_obj = Channel.objects.get(name=channel_data['name'], experiment=experiment_obj)

                    # Save source and related channels if they are valid
                    channel_obj = self.add_source_related_channels(channel_obj, experiment_obj, source_channels_objs,
                                                                   related_channels_objs)

                    # Assign permissions to the users primary group and admin group
                    BossPermissionManager.add_permissions_primary_group(self.request.user, channel_obj)
                    BossPermissionManager.add_permissions_admin_group(channel_obj)

                    # Add Lookup key
                    lookup_key = str(collection_obj.pk) + '&' + str(experiment_obj.pk) + '&' + str(channel_obj.pk)
                    boss_key = collection_obj.name + '&' + experiment_obj.name + '&' + channel_obj.name
                    LookUpKey.add_lookup(lookup_key, boss_key, collection_obj.name, experiment_obj.name,
                                         channel_obj.name)

                    serializer = ChannelReadSerializer(channel_obj)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return BossHTTPError("{}".format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)
            else:
                return BossPermissionError('add', experiment)
        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except Experiment.DoesNotExist:
            return BossResourceNotFoundError(experiment)
        except Channel.DoesNotExist:
            return BossResourceNotFoundError(channel)
        except BossError as err:
            return err.to_http()
        except ValueError:
            return BossHTTPError("Value Error in post data", ErrorCodes.TYPE_ERROR)

    @transaction.atomic
    def put(self, request, collection, experiment, channel):
        """
        Update new Channel
        Args:
            request: DRF Request object
            collection: Collection name
            experiment: Experiment name
            channel: Channel name

        Returns :
            Channel
        """
        if 'name' in request.data:
            channel_name = request.data['name']
        else:
            channel_name = channel
        try:
            # Check if the object exists
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_obj = Channel.objects.get(name=channel, experiment=experiment_obj)

            if request.user.has_perm("update", channel_obj):

                # The source and related channels are names and need to be removed from the dict before serialization
                source_channels = request.data.pop('sources', [])
                related_channels = request.data.pop('related', [])

                # Validate the source and related channels if they are incuded
                channels = self.validate_source_related_channels(experiment_obj, source_channels, related_channels)
                source_channels_objs = channels[0]
                related_channels_objs = channels[1]

                serializer = ChannelUpdateSerializer(channel_obj, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()

                    channel_obj = Channel.objects.get(name=channel_name, experiment=experiment_obj)
                    # Save source and related channels if they are valid
                    channel_obj = self.update_source_related_channels(channel_obj, experiment_obj, source_channels_objs,
                                                                      related_channels_objs)

                    # update the lookup key if you update the name
                    if 'name' in request.data and request.data['name'] != channel:
                        lookup_key = str(collection_obj.pk) + '&' + str(experiment_obj.pk) + '&' \
                                     + str(channel_obj.pk)
                        boss_key = collection_obj.name + '&' + experiment_obj.name + '&' + request.data['name']
                        LookUpKey.update_lookup(lookup_key, boss_key, collection_obj.name,  experiment_obj.name,
                                                request.data['name'])

                    # return the object back to the user
                    channel = serializer.data['name']
                    channel_obj = Channel.objects.get(name=channel, experiment=experiment_obj)
                    serializer = ChannelReadSerializer(channel_obj)
                    return Response(serializer.data)
                else:
                    return BossHTTPError("{}".format(serializer.errors), ErrorCodes.INVALID_POST_ARGUMENT)
            else:
                return BossPermissionError('update', channel)

        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except Experiment.DoesNotExist:
            return BossResourceNotFoundError(experiment)
        except Channel.DoesNotExist:
            return BossResourceNotFoundError(channel)

    @transaction.atomic
    @check_role("resource-manager")
    def delete(self, request, collection, experiment, channel):
        """
        Delete a Channel
        Args:
            request: DRF Request object
            collection: Collection name
            experiment: Experiment name
            channel: Channel name

        Returns :
            Http status
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_obj = Channel.objects.get(name=channel, experiment=experiment_obj)

            if request.user.has_perm("delete", channel_obj):

                # The channel cannot be deleted if this is the source of any other channels
                derived_channels = channel_obj.get_derived()
                if len(derived_channels) > 0:
                    return BossHTTPError("Channel {} is the source channel of other channels and cannot be deleted"
                                         .format(channel), ErrorCodes.INTEGRITY_ERROR)
                channel_obj.to_be_deleted = datetime.now()
                channel_obj.save()
                return HttpResponse(status=204)
            else:
                return BossPermissionError('delete', channel)

        except Collection.DoesNotExist:
            return BossResourceNotFoundError(collection)
        except Experiment.DoesNotExist:
            return BossResourceNotFoundError(experiment)
        except Channel.DoesNotExist:
            return BossResourceNotFoundError(channel)
        except ProtectedError:
            return BossHTTPError("Cannot delete {}. It has channels that reference it.".format(channel),
                                 ErrorCodes.INTEGRITY_ERROR)


class CollectionList(generics.ListAPIView):
    """
    List all collections or create a new collection

    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

    def list(self, request, *args, **kwargs):
        """
        Display only objects that a user has access to
        Args:
            request: DRF request
            *args:
            **kwargs:

        Returns: Collections that user has view permissions on

        """
        # queryset = self.get_queryset()
        collections = get_objects_for_user(request.user, 'read', klass=Collection).exclude(to_be_deleted__isnull=False)
        data = {"collections": [collection.name for collection in collections]}
        return Response(data)


class ExperimentList(generics.ListAPIView):
    """
    List all experiments
    """

    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer

    def list(self, request, collection, *args, **kwargs):
        """
        return experiments for the collection that the user has permissions for
        Args:
            request: DRF request
            collection : Collection name
            *args:
            **kwargs:

        Returns: Experiments that user has view permissions on and are not marked for deletion

        """
        collection_obj = Collection.objects.get(name=collection)
        all_experiments = get_objects_for_user(request.user, 'read', klass=Experiment)\
            .exclude(to_be_deleted__isnull=False)
        experiments = all_experiments.filter(collection=collection_obj)
        data = {"experiments": [experiment.name for experiment in experiments]}
        return Response(data)


class ChannelList(generics.ListAPIView):
    """
    List all channels
    """
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer

    def list(self, request, collection, experiment, *args, **kwargs):
        """
        Display only objects that a user has access to
        Args:
            request: DRF request
            collection: Collection Name
            experiment: Experiment Name

            *args:
            **kwargs:

        Returns: Channel that user has view permissions on

        """
        collection_obj = Collection.objects.get(name=collection)
        experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
        channels = get_objects_for_user(request.user, 'read', klass=Channel).filter(experiment=experiment_obj)
        channels= channels.exclude(to_be_deleted__isnull=False)
        data = {"channels": [channel.name for channel in channels]}
        return Response(data)


class CoordinateFrameList(generics.ListCreateAPIView):
    """
    List all coordinate frames
    """
    queryset = CoordinateFrame.objects.all()
    serializer_class = CoordinateFrameSerializer

    def list(self, request, *args, **kwargs):
        """
        Display only objects that a user has access to
        Args:
            request: DRF request
            *args:
            **kwargs:

        Returns: Coordinate frames that user has view permissions on

        """
        # Note: the line below returns all coordinate frames that the user has read permissions on
        #coords = get_objects_for_user(request.user, 'read', klass=CoordinateFrame).exclude(to_be_deleted__isnull=False)
        if 'owner' in request.query_params:
            owner_flag = request.query_params.get('owner', "False")
        else:
            owner_flag = "False"

        if str.capitalize(owner_flag) == "True":
            coords = CoordinateFrame.objects.filter(creator=request.user).exclude(to_be_deleted__isnull=False)
        else:
            coords = CoordinateFrame.objects.all().exclude(to_be_deleted__isnull=False)
        data = {"coords": [coord.name for coord in coords]}
        return Response(data)
