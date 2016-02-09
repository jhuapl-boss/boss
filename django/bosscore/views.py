from django.shortcuts import render

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.views import APIView

from bosscore.models import Collection, Experiment, Dataset, Channel, TimeSample, Layer, CoordinateFrame
from bosscore.serializers import CollectionSerializer, ExperimentSerializer, DatasetSerializer, ChannelSerializer, \
    TimeSampleSerializer, LayerSerializer, CoordinateFrameSerializer

# from metadb import MetaDB

import re
import os, sys


from . import metadb
from .bosserror import BossError


def create_metakey(bosskey, metakey):
    """
    Combine the boss data model key and the meta data key to create the new metadata key.
    :param bosskey: Key that links the meta data to the boss data model
    :param metakey: Meta data key
    :return: Bosskey concatenated with the meta data key
    """
    return bosskey + "$" + metakey


def checkargs(webargs):

    """
    Parse and error check the webargs from the metadata service urls
    :param webargs: Web args that represent the datamodel object
    :return:
    """
    m = re.match(r"(?P<col>\w+)/?(?P<exp>\w+)?/?(?P<ds>\w+)?/?(?P<channel>\w+)?/?(?P<ts>\w+)?/?(?P<layer>\w+)?/?$",
                 webargs)
    [col, exp, ds, channel, ts, layer] = [i for i in m.groups()]

    if col and Collection.objects.filter(collection_name=col).exists():
        return True
    else:
        error = "The collection name {} Does not exist.".format(webargs)
        raise BossError(error)


@api_view(['GET', 'POST', 'DELETE', 'PUT'])
def boss_meta(request, webargs):
    """  Retrieve, Post, Delete or Update metadata related to the boss data model
    :param webargs: Web args that represent the datamodel object
    :return:
    """
    print (request.method)
    try:
        valid = checkargs(webargs)
    except BossError:
        return HttpResponseBadRequest("[ERROR]: Invalid arguments.")

    bosskey = webargs.replace("/", "&")
    if request.method == 'GET':

        mdb = metadb.MetaDB("bossmeta")
        mkey = request.GET.get('key', None)

        if mkey:
            combinedkey = create_metakey(bosskey, mkey)
            mdata = mdb.getmeta(combinedkey)
            if mdata:
                return Response(mdata)
            else:
                return HttpResponseBadRequest("[ERROR]- Key {} not found for {}".format(mkey, webargs))

    if request.method == 'POST':

        # generate the new Metakey which combines datamodel keys with the meta data key in the post
        mkey = request.POST.get('metakey')
        metavalue = request.POST.get('value')
        combinedkey = create_metakey(bosskey, mkey)

        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB("bossmeta")
        mdb.writemeta(combinedkey, metavalue)
        return HttpResponse(status=201)

    if request.method == 'DELETE':
        # generate the new Metakey which combines datamodel keys with the meta data key in the post
        mkey = request.POST.get('metakey')
        combinedkey = create_metakey(bosskey, mkey)
        print (combinedkey)
        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB("bossmeta")
        response = mdb.deletemeta(combinedkey)
        if 'Attributes' in response:
            return HttpResponse(status=201)
        else:
            return HttpResponseBadRequest("[ERROR]- Key {} not found for {}".format(mkey, webargs))

    if request.method == 'PUT':
        # generate the new Metakey which combines datamodel keys with the meta data key in the post
        mkey = request.POST.get('metakey')
        metavalue = request.POST.get('value')
        combinedkey = create_metakey(bosskey, mkey)

        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB("bossmeta")
        response = mdb.updatemeta(combinedkey, metavalue)
        if 'Attributes' in response:
            return Response(response['Attributes'])
        else:
            return HttpResponseBadRequest("[ERROR]- Key {} not found for {}".format(mkey, webargs))


@api_view(['GET', 'POST'])
def collectionObj(request, col):
    """
    View to access a collection given collection_name
    :param request:
    :param col: Collection name
    """
    try:
        collection = Collection.objects.get(collection_name=col)
    except Collection.DoesNotExist:
        return HttpResponseBadRequest("[ERROR]- Collection  with name {} not found".format(col))


    if request.method == 'GET':
        serializer = CollectionSerializer(collection)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CollectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        collection.delete()
        return HttpResponse(status=204)


@api_view(['GET', 'POST'])
def experimentObj(request, col, exp):
    """
    Retrieve information about a experiment.
    :param col: Collection name
    :param exp: Experiment name
    :return:
    """
    try:
        col = Collection.objects.get(collection_name=col)
        experiment = Experiment.objects.get(experiment_name=exp, collection=col)
    except (Collection.DoesNotExist, Experiment.DoesNotExist):
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = ExperimentSerializer(experiment)
        return Response(serializer.data)
    return HttpResponse(status=404)


@api_view(['GET', 'POST'])
def datasetObj(request, col, exp, ds):
    """
   Retrieve information about a Dataset
    :param request: Web request
    :param col: Collection name
    :param exp: Experiment name
    :param ds: Dataset name
    :return:
    """
    try:
        col = Collection.objects.get(collection_name=col)
        exp = Experiment.objects.get(experiment_name=exp, collection=col)
        dataset = Dataset.objects.get(dataset_name=ds, experiment=exp)

    except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist):
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = DatasetSerializer(dataset)
        return Response(serializer.data)
    return HttpResponse(status=404)


@api_view(['GET', 'POST'])
def channelObj(request, col, exp, ds, channel):
    """
    Retrieve information about a channel
    :param request: Web request
    :param col: Collection name
    :param exp: Experiment name
    :param ds: Dataset name
    :param channel: Channel name
    :return:
    """
    try:
        col = Collection.objects.get(collection_name=col)
        exp = Experiment.objects.get(experiment_name=exp, collection=col)
        ds = Dataset.objects.get(dataset_name=ds, experiment=exp)
        channel = Channel.objects.get(channel_name=channel, dataset=ds)

    except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist, Channel.DoesNotExist):
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = ChannelSerializer(channel)
        return Response(serializer.data)
    return HttpResponse(status=404)


@api_view(['GET', 'POST'])
def timesampleObj(request, col, exp, ds, channel, ts):
    """
    Retrieve information about a timesample
    :param request:
    :param col: Collection name
    :param exp: Experiment name
    :param ds: Dataset name
    :param channel: Channel name
    :param ts: Timesample name
    :return:
    """
    try:
        col = Collection.objects.get(collection_name=col)
        exp = Experiment.objects.get(experiment_name=exp, collection=col)
        ds = Dataset.objects.get(dataset_name=ds, experiment=exp)
        channel = Channel.objects.get(channel_name=channel, dataset=ds)
        ts = TimeSample.objects.get(ts_name=ts, channel=channel)



    except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist, Channel.DoesNotExist,
            TimeSample.DoesNotExist):
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = TimeSampleSerializer(ts)
        return Response(serializer.data)
    return HttpResponse(status=404)


@api_view(['GET', 'POST'])
def layerObj(request, col, exp, ds, channel, ts, layer):
    """
    Retrieve information about a layer
    :param request:
    :param col: Collection name
    :param exp: Experiment name
    :param ds: Dataset name
    :param channel: Channel name
    :param ts: Timesample name
    :param layer: Layer name
    :return:
    """

    try:
        col = Collection.objects.get(collection_name=col)
        exp = Experiment.objects.get(experiment_name=exp, collection=col)
        ds = Dataset.objects.get(dataset_name=ds, experiment=exp)
        channel = Channel.objects.get(channel_name=channel, dataset=ds)
        ts = TimeSample.objects.get(ts_name=ts, channel=channel)
        layer = Layer.objects.get(layer_name=layer, timesample=ts)


    except (Collection.DoesNotExist, Experiment.DoesNotExist, Dataset.DoesNotExist, Channel.DoesNotExist,
            TimeSample.DoesNotExist, Layer.DoesNotExist):
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = LayerSerializer(layer)
        return Response(serializer.data)
    return HttpResponse(status=404)


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
