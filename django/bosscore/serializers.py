from rest_framework import serializers

from bosscore.models import Collection, Experiment, Dataset, Channel, TimeSample, Layer, CoordinateFrame


class CoordinateFrameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoordinateFrame
        fields = (
            'name', 'description', 'x_extent', 'y_extent', 'z_extent', 'x_voxelsize', 'y_voxelsize',
            'z_voxelsize')


class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ('name', 'description', 'time', 'datatype')


class TimeSampleSerializer(serializers.ModelSerializer):
    layers = LayerSerializer(many=True, read_only=True)

    class Meta:
        model = TimeSample
        fields = ('name', 'description', 'channel', 'layers')


class ChannelSerializer(serializers.ModelSerializer):
    timesamples = TimeSampleSerializer(many=True, read_only=True)

    class Meta:
        model = Channel
        fields = ('name', 'description', 'dataset', 'timesamples')


class DatasetSerializer(serializers.ModelSerializer):
    channels = ChannelSerializer(many=True, read_only=True)
    coord = CoordinateFrameSerializer(read_only=True)

    class Meta:
        model = Dataset
        fields = (
            'name', 'description', 'experiment', 'is_source', 'coord_frame', 'channels', 'coord',
            'default_channel', 'default_time', 'default_layer')


class ExperimentSerializer(serializers.ModelSerializer):
    datasets = DatasetSerializer(many=True, read_only=True)

    class Meta:
        model = Experiment
        fields = (
            'name', 'description', 'collection', 'num_resolution_levels', 'hierarchy_method',
            'datasets')


class CollectionSerializer(serializers.ModelSerializer):
    # experiments = serializers.StringRelatedField(many=True)
    experiments = ExperimentSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = ('name', 'description', 'experiments')
