from django.conf import settings
import bossutils
import random

version = settings.BOSS_VERSION

config = bossutils.configuration.BossConfig()
KVIO_SETTINGS = {"cache_host": config['aws']['cache'],
                 "cache_db": 1,
                 "read_timeout": 86400}

# state settings
STATEIO_CONFIG = {"cache_state_host": config['aws']['cache-state'],
                  "cache_state_db": 1}

# object store settings
OBJECTIO_CONFIG = {"s3_flush_queue": None,
                   "cuboid_bucket": "intTest{}.{}".format(random.randint(0, 999), config['aws']['cuboid_bucket']),
                   "page_in_lambda_function": config['lambda']['page_in_function'],
                   "page_out_lambda_function": config['lambda']['flush_function'],
                   "s3_index_table": "intTest.{}".format(config['aws']['s3-index-table'])}

config = bossutils.configuration.BossConfig()
_, domain = config['aws']['cuboid_bucket'].split('.', 1)
FLUSH_QUEUE_NAME = "intTest.S3FlushQueue.{}".format(domain).replace('.', '-')