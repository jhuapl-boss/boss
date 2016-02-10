from django.shortcuts import render

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.views import APIView

from bosscore.models import Collection, Experiment, Dataset, Channel, TimeSample, Layer, CoordinateFrame
from bosscore.serializers import CollectionSerializer, ExperimentSerializer, DatasetSerializer, ChannelSerializer, \
    TimeSampleSerializer, LayerSerializer, CoordinateFrameSerializer

import re
import os, sys


from . import metadb
from .bosserror import BossError

class CollectionObj(APIView):
    """
    View to access a collection given collection_name
    :param request:
    :param col: Collection name
    """
    def get(self, request,collection):
        """
        View to handle GET requests for metadata

        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :param experiment: Experiment name. default = None
        :param dataset: Dataset name. Default = None
        :return:
        """
        try:
            collectionobj= Collection.objects.get(collection_name=collection)
        except Collection.DoesNotExist:
            return HttpResponseBadRequest("[ERROR]- Collection  with name {} not found".format(collection))

        serializer = CollectionSerializer(collectionobj)
        return Response(serializer.data)
        

    def post(request,collection):
        serializer = CollectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(request,collection):
        try:
            collectionobj= Collection.objects.get(collection_name=collection)
        except Collection.DoesNotExist:
            return HttpResponseBadRequest("[ERROR]- Collection  with name {} not found".format(collection))
        collectionobj.delete()
        return HttpResponse(status=204)

class ExperimentObj(APIView):
    """
    View to access a collection given collection_name
    :param request:
    :param col: Collection name
    """
    def get(self, request,collection, experiment):
        """
        Retrieve information about a experiment.
        :param col: Collection name
        :param exp: Experiment name
        :return:
        """
        try:
            col = Collection.objects.get(collection_name=collection)
            experiment = Experiment.objects.get(experiment_name=experiment, collection=col)
        except (Collection.DoesNotExist, Experiment.DoesNotExist):
            return HttpResponse(status=404)

        serializer = ExperimentSerializer(experiment)
        return Response(serializer.data)
    
 
    def post(request,collection,experiment):
        serializer = ExperimentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(request,collection,experiment):
        try:
            col = Collection.objects.get(collection_name=collection)
            experimentobj = Experiment.objects.get(experiment_name=experiment, collection=collection)
        except (Collection.DoesNotExist, Experiment.DoesNotExist):
            return HttpResponse(status=404)
        
        experimentobj.delete()
        return HttpResponse(status=204)
  


class DatasetObj(APIView):
    """
    View to access a dataset
   
    """
    def get(self, request, collection, experiment, dataset):
        """
        Retrieve information about a dataset.
        :param col: Collection name
        :param exp: Experiment name
        :param exp: Dataset name
        :return:
        """
        try:
            col= Collection.objects.get(collection_name=collection)
            exp = Experiment.objects.get(experiment_name=experiment, collection=col)
            datasetobj = Dataset.objects.get(dataset_name=dataset, experiment=exp)
            
        except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist):
            return HttpResponse(status=404)
            
        if request.method == 'GET':
            serializer = DatasetSerializer(datasetobj)
            return Response(serializer.data)
        return HttpResponse(status=404)

    def post(request,collection,experiment,dataset):
        serializer = DatasetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(request,collection,experiment,dataset):
        try:
            col = Collection.objects.get(collection_name=collection)
            exp = Experiment.objects.get(experiment_name=experiment, collection=col)
            datasetobj = Dataset.objects.get(dataset_name=ds, experiment=exp)

        except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist):
            return HttpResponse(status=404)
        datasetobj.delete()
        return HttpResponse(status=204)




class ChannelObj(APIView):
    """
    View to access a channel

    """
    def get(self, request, collection, experiment, dataset, channel):
        """
        Retrieve information about a channel.
        :param col: Collection name
        :param exp: Experiment name
        :param exp: Dataset name
        :param exp: Channel name
        :return:
        """

        try:
            col = Collection.objects.get(collection_name=collection)
            exp = Experiment.objects.get(experiment_name=experiment, collection=col)
            ds = Dataset.objects.get(dataset_name=dataset, experiment=exp)
            channelobj = Channel.objects.get(channel_name=channel, dataset=ds)

        except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist, Channel.DoesNotExist):
            return HttpResponse(status=404)

        if request.method == 'GET':
            serializer = ChannelSerializer(channelobj)
            return Response(serializer.data)
        return HttpResponse(status=404)

    def post(request,collection,experiment,dataset,channel):
        serializer = DatasetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(request,collection,experiment,dataset,channel):
        try:
            col = Collection.objects.get(collection_name=collection)
            exp = Experiment.objects.get(experiment_name=experiment, collection=col)
            ds = Dataset.objects.get(dataset_name=dataset, experiment=exp)
            channelobj = Channel.objects.get(channel_name=channel, dataset=ds)


        except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist):
            return HttpResponse(status=404)
        
        channelobj.delete()
        return HttpResponse(status=204)



class TimesampleObj(APIView):
    """
    View to access a time sample

    """
    def get(self, request, collection, experiment, dataset, channel, timesample):
        """
        Retrieve information about a channel.
        :param col: Collection name
        :param exp: Experiment name
        :param exp: Dataset name
        :param exp: Channel name
        :param exp: time sample name
        :return:
        """

        try:
            col = Collection.objects.get(collection_name=collection)
            exp = Experiment.objects.get(experiment_name=experiment, collection=col)
            ds = Dataset.objects.get(dataset_name=dataset, experiment=exp)
            channel = Channel.objects.get(channel_name=channel, dataset=ds)
            tsobj = TimeSample.objects.get(ts_name=timesample, channel=channel)

        except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist, Channel.DoesNotExist,
            TimeSample.DoesNotExist):
            return HttpResponse(status=404)

        if request.method == 'GET':
            serializer = TimeSampleSerializer(tsobj)
            return Response(serializer.data)
        return HttpResponse(status=404)

    def post(request,collection,experiment,dataset,channel, timesample):
        serializer = TimeSampleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(request,collection,experiment,dataset,channel,timesample):
        
        try:
            col = Collection.objects.get(collection_name=collection)
            exp = Experiment.objects.get(experiment_name=experiment, collection=col)
            ds = Dataset.objects.get(dataset_name=dataset, experiment=exp)
            channel = Channel.objects.get(channel_name=channel, dataset=ds)
            tsobj = TimeSample.objects.get(ts_name=timesample, channel=channel)

        except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist, Channel.DoesNotExist,
            TimeSample.DoesNotExist):
            return HttpResponse(status=404)
        
        tsobj.delete()
        return HttpResponse(status=204)


class LayerObj(APIView):
    """
    View to access a time sample

    """
    def get(self, request, collection, experiment, dataset, channel, timesample, layer):
        """
        Retrieve information about a channel.
        :param col: Collection name
        :param exp: Experiment name
        :param exp: Dataset name
        :param exp: Channel name
        :param exp: time sample name
        :param exp: Layer name
        :return:
        """
        try:
            col = Collection.objects.get(collection_name=collection)
            exp = Experiment.objects.get(experiment_name=experiment, collection=col)
            ds = Dataset.objects.get(dataset_name=dataset, experiment=exp)
            channel = Channel.objects.get(channel_name=channel, dataset=ds)
            ts = TimeSample.objects.get(ts_name=timesample, channel=channel)
            layerobj = Layer.objects.get(layer_name=layer, timesample=ts)


        except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist, Channel.DoesNotExist,
            TimeSample.DoesNotExist, Layer.DoesNotExist):
            return HttpResponse(status=404)

        if request.method == 'GET':
            serializer = LayerSerializer(layerobj)
            return Response(serializer.data)
        return HttpResponse(status=404)

    def post(request,collection,experiment,dataset,channel, timesample, layer):
        serializer = LayerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(request,collection,experiment,dataset,channel,timesample,layer):
        try:
            col = Collection.objects.get(collection_name=collection)
            exp = Experiment.objects.get(experiment_name=experiment, collection=col)
            ds = Dataset.objects.get(dataset_name=dataset, experiment=exp)
            channel = Channel.objects.get(channel_name=channel, dataset=ds)
            ts = TimeSample.objects.get(ts_name=timesample, channel=channel)
            layerobj = Layer.objects.get(layer_name=layer, timesample=ts)


        except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist, Channel.DoesNotExist,
            TimeSample.DoesNotExist, Layer.DoesNotExist):
            return HttpResponse(status=404)

        tsobj.delete()
        return HttpResponse(status=204)



class CollectionList(generics.ListCreateAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


class ExperimentList(generics.ListCreateAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer


class DatasetList(generics.ListCreateAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer


class ChannelList(generics.ListCreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


class TimeSampleList(generics.ListCreateAPIView):
    queryset = TimeSample.objects.all()
    serializer_class = TimeSampleSerializer


class LayerList(generics.ListCreateAPIView):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer


class CoordinateFrameList(generics.ListCreateAPIView):
    queryset = CoordinateFrame.objects.all()
    serializer_class = CoordinateFrameSerializer

class BossMeta(APIView):
    """
    View to handle read,write,update and delete metadata queries
    
    """
    def get_bosskey(self, request,collection,experiment,dataset):
        try :
            if collection:
                # Check if the collection exists
                col = Collection.objects.get(collection_name=collection)
                bosskey = collection
            else:
                # The collection name is None
                return HttpResponse(status=404)

            if experiment:
                # Check if the experiment exists
                exp = Experiment.objects.get(experiment_name=experiment, collection = col)
                bosskey += "&" + experiment
            else:
                # Experiment is None
                return bosskey
            

            if dataset:
                ds = Dataset.objects.get(dataset_name=dataset, experiment=exp)
                bosskey += "&" + dataset
            else:
                return bosskey
            
            if 'layer' in request.query_params:
                #get channel and timesample
                if 'channel' in request.query_params:
                    channel = request.query_params['channel']
                else:
                    default_channel = (ds.default_channel)
                    channel = default_channel.channel_name
                
                if 'timesample' in request.query_params:
                    timesample = request.query_params['timesample']
                else:
                    #TODO - verify error checking  if default_ts is none
                    default_ts = (ds.default_timesample)
                    time = default_ts.timesample_name
                
                layer = request.query_params['layer']
                layerobj = Layer.objects.get(layer_name = layer) 

                #Update the key for boss
                bosskey = bosskey + "&" + channel + "&" + time + "&" + layer
                return bosskey

            if 'timesample' in request.query_params:
                #get channel and timesample
                if 'channel' in request.query_params:
                    channel = request.query_params['channel']
                else:
                    default_channel = (ds.default_channel)
                    channel = default_channel.channel_name

                ts = request.query_params['timesample']
                tsobj = TimeSample.objects.get(timesample_name = layer, channel = default_channel)

                #Update the key for boss
                bosskey = bosskey + "&" + channel + "&"+ time
                
            if 'channel' in request.query_params:
                #get channel and timesample
                channel = request.query_params['channel']
                channelobj = Channel.objects.get(channel_name = channel, dataset = ds)

                #Update the key for boss
                bosskey = bosskey + "&" + channel 
                return bosskey

            return bosskey

                
        except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist, Channel.DoesNotExist,TimeSample.DoesNotExist, Layer.DoesNotExist):
            return HttpResponse(status=404)
            

    def get_combinedkey(self,bosskey,metakey):
        """
        Generate a new metakey which is a combiniation of the datamodel representation and metaday key

        :param bosskey: This represents the datamodel object to attach the metadata to. I
        :param metakey: Meta data key
        :return: new meta key
        """
        return (bosskey + "#" +metakey)

    def get(self, request, collection, experiment=None, dataset= None ):
        """
        View to handle GET requests for metadata 
        ​
        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :param experiment: Experiment name. default = None
        :param dataset: Dataset name. Default = None 
        :return:
        """

        # The metadata consist of two parts. The bosskey#metakey
        # bosskey represents the datamodel object
        # Metakey is the key for the meta data associated with the data model object

        bosskey = self.get_bosskey(request,collection,experiment,dataset)
        if bosskey == None or 'metakey' not in request.query_params:
            # TODO raise Bosserror
            return HttpResponse(status=404)
        mkey = request.query_params['metakey']
        combinedkey = self.get_combinedkey(bosskey,mkey)
        
        mdb = metadb.MetaDB("bossmeta")
        mdata = mdb.getmeta(combinedkey)
        if mdata:
            return Response(mdata)
        else:
            return HttpResponseBadRequest("[ERROR]- Key {} not found".format(mkey))
            
        
    def post(self, request, collection, experiment=None, dataset= None ):
        """
        View to handle POST requests for metadata
        
        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :param experiment: Experiment name. default = None
        :param dataset: Dataset name. Default = None
        :return:
        """

        # The metadata consist of two parts. The bosskey#metakey
        # bosskey represents the datamodel object
        # Metakey is the key for the meta data associated with the data model object

        bosskey = self.get_bosskey(request,collection,experiment,dataset)
        if bosskey == None or 'metakey' not in request.query_params or 'metavalue' not in request.query_params:
            # TODO raise Bosserror
            return HttpResponse(status=404)
        mkey = request.query_params['metakey']
        metavalue = request.query_params['metavalue']

        # generate the new Metakey which combines datamodel keys with the meta data key in the post
        combinedkey = self.get_combinedkey(bosskey, mkey)

        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB("bossmeta")
        mdb.writemeta(combinedkey, metavalue)
        return HttpResponse(status=201)


    def delete(self, request, collection, experiment=None, dataset= None ):
        """
        View to handle the delete requests for metadata

        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :param experiment: Experiment name. default = None
        :param dataset: Dataset name. Default = None
        :return:
        """
        #Get the concatenated key
        bosskey = self.get_bosskey(request,collection,experiment,dataset)
        if bosskey == None or 'metakey' not in request.query_params :
            # TODO raise Bosserror
            return HttpResponse(status=404)
        mkey = request.query_params['metakey']

        # generate the new Metakey which combines datamodel keys with the meta data key in the post
        combinedkey = self.get_combinedkey(bosskey, mkey)

        # Delete metadata from the dynamodb database
        mdb = metadb.MetaDB("bossmeta")
        response = mdb.deletemeta(combinedkey)
        if 'Attributes' in response:
            return HttpResponse(status=201)
        else:
            return HttpResponseBadRequest("[ERROR]- Key {} not found ".format(mkey))
           
    def put(self, request, collection, experiment=None, dataset= None ):
        """
        View to handle update requests for metadata
        
        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :param experiment: Experiment name. default = None
        :param dataset: Dataset name. Default = None
        :return:
        """
        
        # The metadata consist of two parts. The bosskey#metakey
        # bosskey represents the datamodel object
        # Metakey is the key for the meta data associated with the data model object
        
        
        bosskey = self.get_bosskey(request,collection,experiment,dataset)
        if bosskey == None or 'metakey' not in request.query_params or 'metavalue' not in request.query_params:
            # TODO raise Bosserror
            return HttpResponse(status=404)
        mkey = request.query_params['metakey']
        metavalue = request.query_params['metavalue']
            
        # generate the new Metakey which combines datamodel keys with the meta data key in the post
        combinedkey = self.get_combinedkey(bosskey, mkey)
            
        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB("bossmeta")
        mdb.updatemeta(combinedkey, metavalue)
        return HttpResponse(status=201)
