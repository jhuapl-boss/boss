
from .serializers import BossLookupSerializer
from .models import BossLookup

class LookUpKey:
    """
    Bosskey manager

    """

    @staticmethod
    def add_lookup(lookup_key, boss_key, collection_name, experiment_name=None, channel_layer_name=None, max_time_sample= None):
        # Create the boss lookup key

        lookup_data = {'lookup_key':lookup_key , 'boss_key': boss_key,
                       'collection_name': collection_name,
                       'experiment_name': experiment_name,
                       'channel_layer_name': channel_layer_name
                       }
        serializer = BossLookupSerializer(data=lookup_data)
        if serializer.is_valid():
            serializer.save()

            if collection_name and experiment_name and channel_layer_name and max_time_sample:
                # Add lookup keys for all timesamples for the channel and layer
                for time in range(max_time_sample+1):
                    lookup_data['lookup_key'] = lookup_key + '&' + str(time)
                    lookup_data['boss_key'] = boss_key + '&' + str(time)

                    serializer = BossLookupSerializer(data=lookup_data)
                    if serializer.is_valid():
                        serializer.save()
    @staticmethod
    def get_lookup_key(bkey):
        """

        Args:
            bosskey:

        Returns:

        """

        lookup_obj = BossLookup.objects.get(boss_key=bkey)
        return lookup_obj.lookup_key











