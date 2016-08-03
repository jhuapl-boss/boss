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

from .base import *

"""
Run the boss in production.
"""

import bossutils

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

from bossutils.aws import *
aws_mngr = get_aws_manager()

INSTALLED_APPS.append("djangooidc")
INSTALLED_APPS.append("rest_framework.authtoken")
AUTHENTICATION_BACKENDS.insert(1, 'bossoidc.backend.OpenIdConnectBackend')

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'rest_framework.authentication.SessionAuthentication',
    'rest_framework.authentication.TokenAuthentication',
    'oidc_auth.authentication.BearerTokenAuthentication',
)

auth_uri = vault.read('secret/endpoint/auth', 'url')
client_id = vault.read('secret/endpoint/auth', 'client_id')
public_uri = vault.read('secret/endpoint/auth', 'public_uri')

OIDC_VERIFY_SSL = not (config['auth']['OIDC_VERIFY_SSL'] in ['False', 'false'])

LOAD_USER_ROLE = 'bosscore.privileges.load_user_role'
from bossoidc.settings import *
configure_oidc(auth_uri, client_id, public_uri)

