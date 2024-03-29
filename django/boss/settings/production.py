# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory
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

from .base import *
from bossoidc2.settings import BOSSOIDC_LOGIN_URL, BOSSOIDC_LOGOUT_URL

"""
Run the boss in production.
"""

import bossutils
bossutils.logger.configure()

vault = bossutils.vault.Vault()
config = bossutils.configuration.BossConfig()

SECRET_KEY = vault.read('secret/endpoint/django', 'secret_key')

DEBUG = False

# ToDo: update with actual allowed host names.
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': vault.read('secret/endpoint/django/db', 'name'),
        'USER': vault.read('secret/endpoint/django/db', 'user'),
        'PASSWORD': vault.read('secret/endpoint/django/db', 'password'),
        'HOST': config['aws']['db'],
        'PORT': vault.read('secret/endpoint/django/db', 'port'),
    }
}

if config['aws']['cache-session'] != '':
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://{}:6379/{}".format(
                config['aws']['cache-session'], config['aws']['cache-session-db']),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }

    # DP ???: Are these needed, it looks like they just ensure that the default cache is used
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

# Set this here so it's not overriden by any other settings files.
LOGIN_URL = BOSSOIDC_LOGIN_URL
LOGOUT_URL = BOSSOIDC_LOGOUT_URL

INSTALLED_APPS.append("bossoidc2")
INSTALLED_APPS.append("mozilla_django_oidc")
INSTALLED_APPS.append("rest_framework.authtoken")

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'mozilla_django_oidc.contrib.drf.OIDCAuthentication',
    'rest_framework.authentication.SessionAuthentication',
    'boss.authentication.TokenAuthentication',
    'oidc_auth.authentication.BearerTokenAuthentication',
)

AUTHENTICATION_BACKENDS.insert(1, 'bossoidc2.backend.OpenIdConnectBackend') 

auth_uri = vault.read('secret/endpoint/auth', 'url')
client_id = vault.read('secret/endpoint/auth', 'client_id')
public_uri = vault.read('secret/endpoint/auth', 'public_uri')

OIDC_OP_AUTHORIZATION_ENDPOINT = auth_uri + '/protocol/openid-connect/auth'
OIDC_OP_TOKEN_ENDPOINT = auth_uri + '/protocol/openid-connect/token'
OIDC_OP_USER_ENDPOINT = auth_uri + '/protocol/openid-connect/userinfo'
LOGIN_REDIRECT_URL = public_uri + 'v1/mgmt'
LOGOUT_REDIRECT_URL = auth_uri + '/protocol/openid-connect/logout?redirect_uri=' + public_uri
OIDC_RP_CLIENT_ID = client_id
OIDC_RP_CLIENT_SECRET = ''
OIDC_RP_SCOPES = 'email openid profile'
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_OP_JWKS_ENDPOINT = auth_uri + '/protocol/openid-connect/certs'
OIDC_VERIFY_SSL = not (config['auth']['OIDC_VERIFY_SSL'] in ['False', 'false'])
# Fields to look for in the userinfo returned from Keycloak
OIDC_CLAIMS_VERIFICATION = 'preferred_username sub email'

# Allow this user to not have an email address during OIDC claims verification.
KEYCLOAK_ADMIN_USER = 'bossadmin'

LOAD_USER_ROLES = 'bosscore.privileges.load_user_roles'

from bossoidc2.settings import configure_oidc
configure_oidc(auth_uri, client_id, public_uri)

# Load params for spatialDB once during settings.py
# kvio settings
KVIO_SETTINGS = {"cache_host": config['aws']['cache'],
                 "cache_db": int(config['aws']['cache-db']),
                 "read_timeout": 1209600}  # two weeks.

# state settings
STATEIO_CONFIG = {"cache_state_host": config['aws']['cache-state'],
                  "cache_state_db": int(config['aws']['cache-state-db'])}

# object store settings
OBJECTIO_CONFIG = {"s3_flush_queue": config['aws']['s3-flush-queue'],
                   "cuboid_bucket": config['aws']['cuboid_bucket'],
                   "page_in_lambda_function": config['lambda']['page_in_function'],
                   "page_out_lambda_function": config['lambda']['flush_function'],
                   "ingest_lambda_function": config['lambda']['ingest_function'],
                   "s3_index_table": config['aws']['s3-index-table'],
                   "id_index_table": config['aws']['id-index-table'],
                   "id_count_table": config['aws']['id-count-table'],
                   "prod_mailing_list": config["aws"]["prod_mailing_list"],
                   "id_index_new_chunk_threshold": config["aws"]["id-index-new-chunk-threshold"],
                   "index_deadletter_queue": config["aws"]["index-deadletter-queue"],
                   "index_cuboids_keys_queue": config["aws"]["index-cuboids-keys-queue"]
                   }
