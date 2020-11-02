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
from bossoidc2.settings import BOSSOIDC_LOGIN_URL, BOSSOIDC_LOGOUT_URL

"""
Run Boss with a local Keycloak instance for testing.
"""

# These are variables used for testing.  Don't copy these to production.py!
LOCAL_KEYCLOAK_TESTING = True
KEYCLOAK_ADMIN_PASSWORD = 'bossadmin'




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

auth_uri = 'http://localhost:8080/auth/realms/BOSS'
client_id = 'endpoint'
public_uri = 'http://localhost:8000'

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

# Fields to look for in the userinfo returned from Keycloak
OIDC_CLAIMS_VERIFICATION = 'preferred_username sub email'

# Allow this user to not have an email address during OIDC claims verification.
KEYCLOAK_ADMIN_USER = 'bossadmin'

# No SSL when running locally during development.
OIDC_VERIFY_SSL = False

LOAD_USER_ROLES = 'bosscore.privileges.load_user_roles'

from bossoidc2.settings import configure_oidc
configure_oidc(auth_uri, client_id, public_uri)
