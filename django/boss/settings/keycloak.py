# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .mysql import *

"""
Run Boss with a local Keycloak instance for testing.
"""

INSTALLED_APPS.append("bossoidc")
INSTALLED_APPS.append("mozilla_django_oidc")
INSTALLED_APPS.append("rest_framework.authtoken")

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'mozilla_django_oidc.contrib.drf.OIDCAuthentication',
    'rest_framework.authentication.SessionAuthentication',
    'boss.authentication.TokenAuthentication',
    'oidc_auth.authentication.BearerTokenAuthentication',
)

AUTHENTICATION_BACKENDS.insert(1, 'mozilla_django_oidc.auth.OIDCAuthenticationBackend') 
AUTHENTICATION_BACKENDS.insert(1, 'bossoidc.backend.OpenIdConnectBackend') 

auth_uri = 'http://localhost:8080'
client_id = 'endpoint'
public_uri = 'http://localhost:8000'

OIDC_OP_AUTHORIZATION_ENDPOINT = auth_uri + '/protocol/openid-connect/auth'
OIDC_OP_TOKEN_ENDPOINT = auth_uri + '/protocol/openid-connect/token'
OIDC_OP_USER_ENDPOINT = auth_uri + '/protocol/openid-connect/userinfo'
OIDC_LOGIN_REDIRECT_URL = public_uri
OIDC_RP_CLIENT_ID = client_id

from bossoidc.settings import configure_oidc
configure_oidc(auth_uri, client_id, public_uri)
