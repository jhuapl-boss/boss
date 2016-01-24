from django.shortcuts import render

from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics

from bossmeta.models import Collection, Experiment, Dataset, Channel, TimeSample, Layer, CoordinateFrame
from bossmeta.serializers import CollectionSerializer, ExperimentSerializer,DatasetSerializer,ChannelSerializer, TimeSampleSerializer, LayerSerializer, CoordinateFrameSerializer

import re

@api_view(['GET'])
def get_collection(request, webargs):
    """
    View to access a collection given collection_name
    """
    try:
        collection = Collection.objects.get(collection_name=webargs)
    except Collection.DoesNotExist:
        return HttpResponse(status=404)

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


@api_view(['GET'])
def get_experiment(request, col, exp):
    """
    General view that parses meta data.
    """
    try:
        col = Collection.objects.get(collection_name= col)
        experiment = Experiment.objects.get(experiment_name = exp , collection = col )
    except Collection.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = ExperimentSerializer(experiment)
        return Response(serializer.data)
    return HttpResponse(status=404)
    
class CollectionList(generics.ListCreateAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

class CollectionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


class ExperimentList(generics.ListCreateAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer

class ExperimentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer


class DatasetList(generics.ListCreateAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer

class DatasetDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer


class ChannelList(generics.ListCreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer

class ChannelDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer

class TimeSampleList(generics.ListCreateAPIView):
    queryset = TimeSample.objects.all()
    serializer_class = TimeSampleSerializer

class TimeSampleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = TimeSample.objects.all()
    serializer_class = TimeSampleSerializer

class LayerList(generics.ListCreateAPIView):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer

class LayerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer

class CoordinateFrameList(generics.ListCreateAPIView):
    queryset = CoordinateFrame.objects.all()
    serializer_class = CoordinateFrameSerializer

class CoordinateFrameDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CoordinateFrame.objects.all()
    serializer_class = CoordinateFrameSerializer
