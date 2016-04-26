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
from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .error import BossError, BossHTTPError
from .lookup import LookUpKey
from .permissions import BossPermissionManager
from .serializers import *


class CollectionDetail(APIView):
    """
    View to access a collection object

    """
    def get(self, request, collection):
        """
        View to handle GET requests for a single instance of a collection

        :param request: DRF Request object
        :param collection: Collection name specifying the collection you want
        :return:
        """

        try:
            collection_obj = Collection.objects.get(name=collection)

            # Check for permissions
            if request.user.has_perm("view_collection", collection_obj):
                serializer = CollectionSerializer(collection_obj)
                return Response(serializer.data)
            else:
                return BossHTTPError(404, "{} does not have the required permissions".format(request.user), 30000)
        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(collection), 30000)

    @transaction.atomic
    def post(self, request, collection):
        """Create a new collection

        View to create a new collection and an associated bosskey for that collection
        Args:
            request: DRF Request object
            collection : Collection name
        Returns:

        """

        # TODO (pmanava1): Apply permissions here
        col_data = request.data
        col_data['name'] = collection

        serializer = CollectionSerializer(data=col_data)
        if serializer.is_valid():
            serializer.save(creator=self.request.user)
            collection = Collection.objects.get(name=col_data['name'])

            # Assign permissions to the users primary group
            BossPermissionManager.add_permissions_primary_group(self.request.user, collection, 'collection')

            lookup_key = collection.pk
            boss_key = collection.name
            LookUpKey.add_lookup(lookup_key, boss_key, collection.name)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return BossHTTPError(409, "{}".format(serializer.errors), 30000)

    @transaction.atomic
    def put(self, request, collection):
        """
        Update a collection using django rest framework

        :param request: DRF Request object
        :param collection: Collection name
        :return:
        """
        col_data = request.data
        col_data['name'] = collection
        # TODO :Check for permissions
        try:
            # Check if the object exists
            collection_obj = Collection.objects.get(name=collection)

            serializer = CollectionSerializer(collection_obj, data=request.data)
            if serializer.is_valid():
                serializer.save()

                # TODO (pmanava1) -  Update boss key if the object name is updated?
                return Response(serializer.data)
            return BossHTTPError(404, "{}".format(serializer.errors), 30000)

        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(collection), 30000)

    @transaction.atomic
    def delete(self, request, collection):
        """
        Delete a collection
        :param request: DRF Request object
        :param collection:  Name of collection to delete
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            if request.user.has_perm("delete_collection", collection_obj):
                collection_obj.delete()

                # delete the lookup key for this object
                LookUpKey.delete_lookup_key(collection, None, None)
                return HttpResponse(status=204)
            else:
                return BossHTTPError(404, "{} does not have the required permissions".format(request.user), 30000)
        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(collection), 30000)
        except ProtectedError:
            return BossHTTPError(404, "Cannot delete {}. It has experiments that reference it.".format(collection),
                                 30000)


class CoordinateFrameDetail(APIView):
    """
    View to access a collection object

    """
    def get(self, request, coordframe):
        """
        View to handle GET requests for a single instance of a coordinateframe

        :param request: DRF Request object
        :param coordframe: Coordinate frame name specifying the coordinate frame you want
        :return:
        """
        try:
            coordframe_obj = CoordinateFrame.objects.get(name=coordframe)
            # Check for permissions
            if request.user.has_perm("view_coordinateframe", coordframe_obj):
                serializer = CoordinateFrameSerializer(coordframe_obj)
                return Response(serializer.data)
            else:
                return BossHTTPError(404, "{} does not have the required permissions".format(request.user), 30000)
        except CoordinateFrame.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(coordframe), 30000)

    @transaction.atomic
    def post(self, request, coordframe):
        """Create a new coordinate frame

        View to create a new coordinate frame
        Args:
            request: DRF Request object
            coordframe : Coordinate frame name
        Returns:

        """
        # TODO (pmanava1): Apply permissions here
        coordframe_data = request.data
        coordframe_data['name'] = coordframe

        serializer = CoordinateFrameSerializer(data=coordframe_data)
        if serializer.is_valid():
            serializer.save(creator=self.request.user)
            coordframe_obj = CoordinateFrame.objects.get(name=coordframe_data['name'])

            # Assign permissions to the users primary group
            BossPermissionManager.add_permissions_primary_group(self.request.user, coordframe_obj, 'coordinateframe')

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return BossHTTPError(409, "{}".format(serializer.errors), 30000)

    @transaction.atomic
    def put(self, request, coordframe):
        """
        Update a coordinate frame using django rest framework

        :param request: DRF Request object
        :param coordframe: Coordinate frame name
        :return:
        """
        coordframe_data = request.data
        coordframe_data['name'] = coordframe
        # TODO :Check for permissions
        try:
            # Check if the object exists
            coordframe_obj = CoordinateFrame.objects.get(name=coordframe)
            serializer = CoordinateFrameSerializer(coordframe_obj, data=request.data, partial=True)
            if serializer.is_valid():

                serializer.save()
                return Response(serializer.data)
            else:
                return BossHTTPError(404, "{}".format(serializer.errors), 30000)

        except CoordinateFrame.DoesNotExist:
            return BossHTTPError(404, "Coordinate frame  with name {} not found".format(coordframe), 30000)

    @transaction.atomic
    def delete(self, request, coordframe):
        """
        Delete a coordinate frame
        :param request: DRF Request object
        :param coordframe:  Name of coordinateframe to delete
        :return:
        """
        try:
            coordframe_obj = CoordinateFrame.objects.get(name=coordframe)
            if request.user.has_perm("delete_coordinateframe", coordframe_obj):
                coordframe_obj.delete()
                return HttpResponse(status=204)
            else:
                return BossHTTPError(404, "{} does not have the required permissions".format(request.user), 30000)
        except CoordinateFrame.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(coordframe), 30000)
        except ProtectedError:
            return BossHTTPError(404, "Cannot delete {}. It has experiments that reference it.".format(coordframe),
                                 30000)


class ExperimentDetail(APIView):
    """
    View to access a collection object

    """
    def get(self, request, collection, experiment):
        """
        View to handle GET requests for a single instance of a experimen

        Args:
            request: DRF Request object
            collection: Collection name specifying the collection you want
            experiment: Experiment name specifying the experiment instance
        Returns :
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            # Check for permissions
            if request.user.has_perm("view_experiment", experiment_obj):
                serializer = ExperimentSerializer(experiment_obj)
                return Response(serializer.data)
            else:
                return BossHTTPError(404, "{} does not have the required permissions".format(request.user), 30000)
        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(collection), 30000)
        except Experiment.DoesNotExist:
            return BossHTTPError(404, "Experiment  with name {} not found".format(experiment), 30000)

    @transaction.atomic
    def post(self, request, collection, experiment):
        """Create a new experiment

        View to create a new experiment and an associated bosskey for that experiment
        Args:
            request: DRF Request object
            collection : Collection name
            experiment : Experiment name
        Returns:

        """

        # TODO (pmanava1): Apply permissions here
        experiment_data = request.data
        experiment_data['name'] = experiment
        try:
            collection_obj = Collection.objects.get(name=collection)

            # Confirm that the collection for post data and request are the same
            if 'collection' in experiment_data:
                if collection_obj.pk != int(experiment_data['collection']):
                    return BossHTTPError(404, "The collection name {} in the request does not match"
                                              " the collection in the post data".format(collection), 30000)
            else:
                experiment_data['collection'] = collection_obj.pk

            serializer = ExperimentSerializer(data=experiment_data)
            if serializer.is_valid():
                serializer.save(creator=self.request.user)
                experiment_obj = Experiment.objects.get(name=experiment_data['name'])

                # Assign permissions to the users primary group
                BossPermissionManager.add_permissions_primary_group(self.request.user, experiment_obj, 'experiment')

                lookup_key = str(collection_obj.pk) + '&' + str(experiment_obj.pk)
                boss_key = collection_obj.name + '&' + experiment_obj.name
                LookUpKey.add_lookup(lookup_key, boss_key, collection_obj.name, experiment_obj.name)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return BossHTTPError(409, "{}".format(serializer.errors), 30000)
        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection with name {} does not exist".format(collection), 30000)
        except ValueError:
            return BossHTTPError(404, "Value Error.Collection id {} in post data needs to "
                                      "be an integer".format(experiment_data['collection']), 30000)

    @transaction.atomic
    def put(self, request, collection, experiment):
        """
        Update a experiment using django rest framework

        Args:
            request: DRF Request object
            collection: Collection name
            experiment : Experiment name for the new experiment

        Returns:
        """
        experiment_data = request.data
        experiment_data['name'] = experiment

        # TODO :Check for permissions
        try:
            # Check if the object exists
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)

            serializer = ExperimentSerializer(experiment_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                # TODO (pmanava1) -  Update boss key if the object name is updated?
                return Response(serializer.data)
            return BossHTTPError(404, "{}".format(serializer.errors), 30000)

        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(collection), 30000)
        except Experiment.DoesNotExist:
            return BossHTTPError(404, "Experiment  with name {} not found".format(experiment), 30000)

    @transaction.atomic
    def delete(self, request, collection, experiment):
        """
        Delete a experiment
        Args:
            request: DRF Request object
            collection:  Name of collection
            experiment: Experiment name to delete
        Returns:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            if request.user.has_perm("delete_experiment", experiment_obj):
                experiment_obj.delete()

                # delete the lookup key for this object
                LookUpKey.delete_lookup_key(collection, experiment, None)
                return HttpResponse(status=204)
            else:
                return BossHTTPError(404, "{} does not have the required permissions".format(request.user), 30000)
        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(collection), 30000)
        except Experiment.DoesNotExist:
            return BossHTTPError(404, "Experiment  with name {} not found".format(experiment), 30000)
        except ProtectedError:
            return BossHTTPError(404, "Cannot delete {}. It has channels or layers that reference "
                                      "it.".format(experiment), 30000)


class ChannelLayerDetail(APIView):
    """
    View to access a channel

    """

    def get(self, request, collection, experiment, channel_layer):
        """
        Retrieve information about a channel.
        Args:
            request: DRF Request object
            collection: Collection name
            experiment: Experiment name
            channel_layer: Channel or Layer name

        Returns :
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_layer_obj = ChannelLayer.objects.get(name=channel_layer, experiment=experiment_obj)

            # Check for permissions
            if request.user.has_perm("view_channellayer", channel_layer_obj):
                serializer = ChannelLayerSerializer(channel_layer_obj)
                return Response(serializer.data)
            else:
                return BossHTTPError(404, "{} does not have the required permissions".format(request.user), 30000)

        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} is not found".format(collection), 30000)
        except Experiment.DoesNotExist:
            return BossHTTPError(404, "Experiment  with name {} is not found".format(experiment), 30000)
        except ChannelLayer.DoesNotExist:
            return BossHTTPError(404, "A Channel or layer  with name {} is not found".format(channel_layer), 30000)

    def post(self, request, collection, experiment, channel_layer):
        """
        Post a new Channel
        Args:
            request: DRF Request object
            collection: Collection name
            experiment: Experiment name
            channel_layer: Channel or Layer name

        Returns :
        """
        # TODO (pmanava1): Apply permissions here
        channel_layer_data = request.data
        channel_layer_data['name'] = channel_layer

        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)

            # Confirm that the experiment for post data and request are the same
            if 'experiment' in channel_layer_data:
                if experiment_obj.pk != int(channel_layer_data['experiment']):
                    return BossHTTPError(404, "The experiment name {} in the request does not match"
                                              " the experiment in the post data".format(experiment), 30000)
            else:
                channel_layer_data['experiment'] = experiment_obj.pk

            serializer = ChannelLayerSerializer(data=channel_layer_data)
            if serializer.is_valid():
                serializer.save(creator=self.request.user)



                channel_layer_obj = ChannelLayer.objects.get(name=channel_layer_data['name'], experiment=experiment_obj)

                # Assign permissions to the users primary group
                BossPermissionManager.add_permissions_primary_group(self.request.user, channel_layer_obj,
                                                                    'channellayer')

                # Add Lookup key
                lookup_key = str(collection_obj.pk) + '&' + str(experiment_obj.pk) + '&' + str(channel_layer_obj.pk)
                boss_key = collection_obj.name + '&' + experiment_obj.name + channel_layer_obj.name
                LookUpKey.add_lookup(lookup_key, boss_key, collection_obj.name, experiment_obj.name,
                                     channel_layer_obj.name)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return BossHTTPError(409, "{}".format(serializer.errors), 30000)
        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection with name {} does not exist".format(collection), 30000)
        except Experiment.DoesNotExist:
            return BossHTTPError(404, "Experiment with name {} does not exist".format(experiment), 30000)
        except ValueError:
            return BossHTTPError(404, "Value Error.Collection id {} in post data needs to "
                                      "be an integer".format(channel_layer_data['experiment']), 30000)

    def put(self, request, collection, experiment, channel_layer):
        """
        Update new Channel or Layer
        Args:
            request: DRF Request object
            collection: Collection name
            experiment: Experiment name
            channel_layer: Channel or Layer name

        Returns :
        """
        channel_layer_data = request.data
        channel_layer_data['name'] = channel_layer

        # TODO :Check for permissions
        try:
            # Check if the object exists
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_layer_obj = ChannelLayer.objects.get(name=channel_layer, experiment=experiment_obj)

            serializer = ChannelLayerSerializer(channel_layer_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                # TODO (pmanava1) -  Update boss key if the object name is updated?
                return Response(serializer.data)
            return BossHTTPError(404, "{}".format(serializer.errors), 30000)

        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(collection), 30000)
        except Experiment.DoesNotExist:
            return BossHTTPError(404, "Experiment  with name {} not found".format(experiment), 30000)
        except ChannelLayer.DoesNotExist:
            return BossHTTPError(404, "Experiment  with name {} not found".format(channel_layer), 30000)

    def delete(self, request, collection, experiment, channel_layer):
        """
        Delete a Channel
        Args:
            request: DRF Request object
            collection: Collection name
            experiment: Experiment name
            channel_layer: Channel or Layer name

        Returns :
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_layer_obj = ChannelLayer.objects.get(name=channel_layer, experiment=experiment_obj)

            # TODO (pmanava1) _ delete bosslookup
            if request.user.has_perm("delete_channellayer", channel_layer_obj):
                channel_layer_obj.delete()
                return HttpResponse(status=204)
            else:
                return BossHTTPError(404, "{} does not have the required permissions".format(request.user), 30000)

        except Collection.DoesNotExist:
            return BossHTTPError(404, "Collection  with name {} not found".format(collection), 30000)
        except Experiment.DoesNotExist:
            return BossHTTPError(404, "Experiment  with name {} not found".format(experiment), 30000)
        except ChannelLayer.DoesNotExist:
            return BossHTTPError(404, "Experiment  with name {} not found".format(channel_layer), 30000)


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
        collections = get_objects_for_user(request.user, 'view_collection', klass=Collection)
        serializer = CollectionSerializer(collections, many=True)
        return Response(serializer.data)


class ExperimentList(generics.ListAPIView):
    """
    List all experiments
    """

    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer

    def list(self, request, collection,  *args, **kwargs):
        """
        return experiments for the collection that the user has permissions for
        Args:
            request: DRF request
            collection : Collection name
            *args:
            **kwargs:

        Returns: Experiments that user has view permissions on

        """
        collection_obj = Collection.objects.get(name=collection)
        all_experiments = get_objects_for_user(request.user, 'view_experiment', klass=Experiment)
        experiments = all_experiments.filter(collection=collection_obj)
        serializer = ExperimentSerializer(experiments, many=True)
        return Response(serializer.data)


class ChannelList(generics.ListAPIView):
    """
    List all channels
    """
    queryset = ChannelLayer.objects.all()
    serializer_class = ChannelLayerSerializer

    def list(self,request, collection, experiment, *args, **kwargs):
        """
        Display only objects that a user has access to
        Args:
            request: DRF request
            collection: Collection Name
            experiment: Experiment Name

            *args:
            **kwargs:

        Returns: Channel_Layers that user has view permissions on

        """
        collection_obj = Collection.objects.get(name=collection)
        experiment_obj = Experiment.objects.get(name=experiment, collection= collection_obj)
        channel_layers = get_objects_for_user(request.user, 'view_channellayer',
                                              klass=ChannelLayer).filter(is_channel=True, experiment=experiment_obj)
        serializer = ChannelLayerSerializer(channel_layers, many=True)
        return Response(serializer.data)


class LayerList(generics.ListAPIView):
    """
    List all layers
    """
    queryset = ChannelLayer.objects.filter(is_channel=False)
    serializer_class = LayerSerializer

    def list(self, request, *args, **kwargs):
        """
        Display only objects that a user has access to
        Args:
            request: DRF request
            *args:
            **kwargs:

        Returns: Channel_Layers that user has view permissions on

        """
        channel_layers = get_objects_for_user(request.user, 'view_channellayer',
                                              klass=ChannelLayer).filter(is_channel=False)
        serializer = ChannelLayerSerializer(channel_layers, many=True)
        return Response(serializer.data)


class CoordinateFrameList(generics.ListCreateAPIView):
    """
    List all coordinate frames
    """
    queryset = CoordinateFrame.objects.all()
    serializer_class = CoordinateFrameSerializer


