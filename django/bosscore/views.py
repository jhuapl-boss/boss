from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.views import APIView

from .models import *
from .serializers import *
from .error import BossError, BossHTTPError

from . import metadb
from .request import BossRequest


class CollectionObj(APIView):
    """
    View to access a collection object

    """
    def get(self, request, collection):
        """
        View to handle GET requests for a Collection

        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
        except Collection.DoesNotExist:
            return HttpResponseBadRequest("[ERROR]- Collection  with name {} not found".format(collection))

        serializer = CollectionSerializer(collection_obj)
        return Response(serializer.data)

    def post(self,request, collection):
        """
        Post a new collection using django rest framework

        :param request: DRF Request object
        :param collection: Collection name
        :return:
        """
        serializer = CollectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, collection):
        """
        Delete a collection
        :param request: DRF Request object
        :param collection:  Name of collection to delete
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
        except Collection.DoesNotExist:
            return HttpResponseBadRequest("[ERROR]- Collection  with name {} not found".format(collection))
        collection_obj.delete()
        return HttpResponse(status=204)


class ExperimentObj(APIView):
    """
    View to access an experiment object

    """

    def get(self, request, collection, experiment):
        """
        Retrieve information about a experiment.
        :param request: DRF Request object
        :param collection: Collection name
        :param experiment: Experiment name
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
        except (Collection.DoesNotExist, Experiment.DoesNotExist):
            return HttpResponse(status=404)

        serializer = ExperimentSerializer(experiment_obj)
        return Response(serializer.data)

    def post(self, request, collection, experiment):
        """
        Post  a new experiment
        :param request: DRF Request object
        :param collection: Collection name
        :param experiment: Experiment name
        :return:
        """
        serializer = ExperimentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, collection, experiment):
        """
        Delete an experiment object given the collection and experiment name
        :param request: DRF Request object
        :param collection: Collection Name
        :param experiment: Experiment Name
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
        except (Collection.DoesNotExist, Experiment.DoesNotExist):
            return HttpResponse(status=404)

        experiment_obj.delete()
        return HttpResponse(status=204)


class ChannelLayerObj(APIView):
    """
    View to access a channel

    """

    def get(self, request, collection, experiment, channel_layer):
        """
        Retrieve information about a channel.
        :param request: DRF Request object
        :param collection: Collection name
        :param experiment: Experiment name
        :param channel_layer: Channel or Layer name
        :return:
        """

        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_layer_obj = ChannelLayer.objects.get(name=channel_layer, experiment=experiment_obj)

        except (Collection.DoesNotExist, Experiment.DoesNotExist, ChannelLayer.DoesNotExist):
            return HttpResponse(status=404)

        if request.method == 'GET':
            serializer = ChannelLayerSerializer(channel_layer_obj)
            return Response(serializer.data)
        return HttpResponse(status=404)

    def post(self, request, collection, experiment, channel_layer):
        """
        Post a new Channel
        :param request: DRF Request object
        :param collection: Collection
        :param experiment: Experiment
        :param channel_layer: Channel or Layer
        :return:
        """
        serializer = ChannelLayerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, collection, experiment, channel_layer):
        """
        Delete a Channel
        :param request: DRF Request object
        :param collection: Collection
        :param experiment: Experiment
        :param channel_layer: Channel or Layer
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_layer_obj = ChannelLayer.objects.get(name=channel_layer, experiment=experiment_obj)
        except (Collection.DoesNotExist, Experiment.DoesNotExist):
            return HttpResponse(status=404)

        channel_layer_obj.delete()
        return HttpResponse(status=204)


class CollectionList(generics.ListCreateAPIView):
    """
    List all collections

    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


class ExperimentList(generics.ListCreateAPIView):
    """
    List all experiments
    """
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer


class ChannelList(generics.ListCreateAPIView):
    """
    List all channels
    """
    queryset = ChannelLayer.objects.all()
    serializer_class = ChannelLayerSerializer


class LayerList(generics.ListCreateAPIView):
    """
    List all layers
    """
    queryset = ChannelLayer.objects.all()
    serializer_class = ChannelLayerSerializer


class CoordinateFrameList(generics.ListCreateAPIView):
    """
    List all coordinate frames
    """
    queryset = CoordinateFrame.objects.all()
    serializer_class = CoordinateFrameSerializer


class BossMeta(APIView):
    """
    View to handle read,write,update and delete metadata queries
    
    """

    def get_combinedkey(self, bosskey, key):
        """
        Generate a new metakey which is a combiniation of the datamodel representation and meta data key

        :param bosskey: This represents the datamodel object to attach the metadata to. I
        :param key: Meta data key
        :return: new meta key
        """
        return (bosskey + "#" + key)

    def get(self, request, collection, experiment=None, dataset=None):
        """
        View to handle GET requests for metadata 
        ​
        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :param experiment: Experiment name. default = None
        :param dataset: Dataset name. Default = None 
        :return:
        """

        # The metadata consist of two parts. The bosskey#key
        # bosskey represents the datamodel object
        # key is the key for the meta data associated with the data model object

        if 'key' not in request.query_params:
            return BossHTTPError(404, "Missing optional argument key in the request", 30000)

        try:
            req = BossRequest(request)
            bosskey = req.get_bosskey()

        except BossError as err:
            return BossHTTPError(err.args[0], err.args[1], err.args[2])

        if bosskey == None:
            return BossHTTPError(404, "Invalid request. Unable to parse the datamodel arguments", 30000)

        mkey = request.query_params['key']
        combinedkey = self.get_combinedkey(bosskey, mkey)

        mdb = metadb.MetaDB("bossmeta")
        mdata = mdb.getmeta(combinedkey)
        if mdata:
            return Response(mdata)
        else:
            return BossHTTPError(404, "Invalid request. Key {} Not found in the database".format(mkey), 30000)

    def post(self, request, collection, experiment=None, dataset=None):
        """
        View to handle POST requests for metadata
        
        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :param experiment: Experiment name. default = None
        :param dataset: Dataset name. Default = None
        :return:
        """

        # The metadata consist of two parts. The bosskey#key
        # bosskey represents the datamodel object
        # key is the key for the meta data associated with the data model object

        if 'key' not in request.query_params or 'value' not in request.query_params:
            return BossHTTPError(404, "Missing optional argument key/value in the request", 30000)

        try:
            req = BossRequest(request)
            bosskey = req.get_bosskey()
        except BossError as err:
            return BossHTTPError(err.args[0], err.args[1], err.args[2])

        if bosskey == None:
            return BossHTTPError(404, "Invalid request. Unable to parse the datamodel arguments", 30000)

        mkey = request.query_params['key']
        value = request.query_params['value']

        # generate the new Metakey which combines datamodel keys with the meta data key in the post
        combinedkey = self.get_combinedkey(bosskey, mkey)
        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB("bossmeta")
        mdb.writemeta(combinedkey, value)
        return HttpResponse(status=201)

    def delete(self, request, collection, experiment=None, dataset=None):
        """
        View to handle the delete requests for metadata

        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :param experiment: Experiment name. default = None
        :param dataset: Dataset name. Default = None
        :return:
        """
        if 'key' not in request.query_params:
            return BossHTTPError(404, "Missing optional argument key in the request", 30000)

        try:
            req = BossRequest(request)
            bosskey = req.get_bosskey()
        except BossError as err:
            return BossHTTPError(err.args[0], err.args[1], err.args[2])

        if bosskey == None:
            return BossHTTPError(404, "Invalid request. Unable to parse the datamodel arguments", 30000)

        mkey = request.query_params['key']

        # generate the new Metakey which combines datamodel keys with the meta data key in the post
        combinedkey = self.get_combinedkey(bosskey, mkey)

        # Delete metadata from the dynamodb database
        mdb = metadb.MetaDB("bossmeta")
        response = mdb.deletemeta(combinedkey)
        if 'Attributes' in response:
            return HttpResponse(status=201)
        else:
            return HttpResponseBadRequest("[ERROR]- Key {} not found ".format(mkey))

    def put(self, request, collection, experiment=None, dataset=None):
        """
        View to handle update requests for metadata
        
        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :param experiment: Experiment name. default = None
        :param dataset: Dataset name. Default = None
        :return:
        """

        # The metadata consist of two parts. The bosskey#key
        # bosskey represents the datamodel object
        # key is the key for the meta data associated with the data model object

        if 'key' not in request.query_params or 'value' not in request.query_params:
            return BossHTTPError(404, "Missing optional argument key/value in the request", 30000)

        try:
            req = BossRequest(request)
            bosskey = req.get_bosskey()
        except BossError as err:
            return BossHTTPError(err.args[0], err.args[1], err.args[2])

        if bosskey == None:
            return BossHTTPError(404, "Invalid request. Unable to parse the datamodel arguments", 30000)

        mkey = request.query_params['key']
        value = request.query_params['value']

        # generate the new metakey which combines the bosskey with the meta data key in the post
        combinedkey = self.get_combinedkey(bosskey, mkey)

        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB("bossmeta")
        mdb.updatemeta(combinedkey, value)
        return HttpResponse(status=201)
