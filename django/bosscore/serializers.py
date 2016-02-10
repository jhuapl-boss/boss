from rest_framework import serializers

from bosscore.models import Collection, Experiment, Dataset, Channel, TimeSample, Layer, CoordinateFrame


class CoordinateFrameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoordinateFrame
        fields = (
            'coord_name', 'coord_description', 'xextent', 'yextent', 'zextent', 'xvoxelsize', 'yvoxelsize',
            'zvoxelsize')


class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ('layer_name', 'layer_description', 'timesample', 'datatype')


class TimeSampleSerializer(serializers.ModelSerializer):
    layers = LayerSerializer(many=True, read_only=True)

    class Meta:
        model = TimeSample
        fields = ('ts_name', 'ts_description', 'channel', 'layers')


class ChannelSerializer(serializers.ModelSerializer):
    timesamples = TimeSampleSerializer(many=True, read_only=True)

    class Meta:
        model = Channel
        fields = ('channel_name', 'channel_description', 'dataset', 'timesamples')


class DatasetSerializer(serializers.ModelSerializer):
    channels = ChannelSerializer(many=True, read_only=True)
    coord = CoordinateFrameSerializer(read_only=True)

    class Meta:
        model = Dataset
        fields = (
        'dataset_name', 'dataset_description', 'experiment', 'is_source', 'coord_frame', 'channels','coord','default_channel','default_timesample','default_layer')


class ExperimentSerializer(serializers.ModelSerializer):
    datasets = DatasetSerializer(many=True, read_only=True)

    class Meta:
        model = Experiment
        fields = (
        'experiment_name', 'experiment_description', 'collection', 'num_resolution_levels', 'heirarchy_method',
        'datasets')


class CollectionSerializer(serializers.ModelSerializer):
    # experiments = serializers.StringRelatedField(many=True)
    experiments = ExperimentSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = ('collection_name', 'collection_description', 'experiments')
