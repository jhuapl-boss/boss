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
from bossoidc.settings import BOSSOIDC_LOGIN_URL, BOSSOIDC_LOGOUT_URL

"""
Run Boss with a local Keycloak instance for testing.
"""

# These are variables used for testing.  Don't copy these to production.py!
LOCAL_KEYCLOAK_TESTING = True
KEYCLOAK_ADMIN_USER = 'bossadmin'
KEYCLOAK_ADMIN_PASSWORD = 'bossadmin'




# Set this here so it's not overriden by any other settings files.
LOGIN_URL = BOSSOIDC_LOGIN_URL
LOGOUT_URL = BOSSOIDC_LOGOUT_URL

INSTALLED_APPS.append("bossoidc")
INSTALLED_APPS.append("mozilla_django_oidc")
INSTALLED_APPS.append("rest_framework.authtoken")

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'mozilla_django_oidc.contrib.drf.OIDCAuthentication',
    'rest_framework.authentication.SessionAuthentication',
    'boss.authentication.TokenAuthentication',
    'oidc_auth.authentication.BearerTokenAuthentication',
)

#AUTHENTICATION_BACKENDS.insert(1, 'mozilla_django_oidc.auth.OIDCAuthenticationBackend') 
AUTHENTICATION_BACKENDS.insert(1, 'bossoidc.backend.OpenIdConnectBackend') 

LOAD_USER_ROLES = 'bosscore.privileges.load_user_roles'

auth_uri = 'http://localhost:8080/auth/realms/BOSS'
client_id = 'endpoint'
public_uri = 'http://localhost:8000'

OIDC_OP_AUTHORIZATION_ENDPOINT = auth_uri + '/protocol/openid-connect/auth'
OIDC_OP_TOKEN_ENDPOINT = auth_uri + '/protocol/openid-connect/token'
OIDC_OP_USER_ENDPOINT = auth_uri + '/protocol/openid-connect/userinfo'
#LOGIN_REDIRECT_URL = public_uri + '/openid/callback/login/'
LOGIN_REDIRECT_URL = public_uri + 'v1/mgmt'
LOGOUT_REDIRECT_URL = auth_uri + '/protocol/openid-connect/logout'
OIDC_RP_CLIENT_ID = client_id
OIDC_RP_CLIENT_SECRET = ''
OIDC_RP_SCOPES = 'sub preferred_username'
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_RP_IDP_SIGN_KEY = (
'''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApgdDYs/B+6XJfuo6mCFW
/JTafaWE9WcDqZd8jB3rj+DEeZuUg+5wS34ih7YAgv/8L09FAL/rdX2DBxS1Ohmo
m5Lu4qmZVHy2Xwu6NHVwozWydilldlvu6vAa9ozMtlNNuTTDTyEgCxLbXHEMEpRd
xVcy5P0kEY2YyvLXAKK5iX+XEnIH3IFbzPBvqwBGneIkGXEYPszXFELaZ2bp0vPI
ZfFdlb4Nv4FwodLNuKLjEoXLHHscoR3zmuzeq5cJ+i2mzInn4kkEdBXHoADTUvot
qMNblmEMW8muwAd4i7e4nvfnSRjq7+bPlb1jEOBDL6nd8cU4ACb/p44k0rBggtFV
aQIDAQAB
-----END PUBLIC KEY-----''')
OIDC_OP_JWKS_ENDPOINT = auth_uri + '/protocol/openid-connect/certs'
# No SSL when running locally during development.
OIDC_VERIFY_SSL = False

from bossoidc.settings import configure_oidc
configure_oidc(auth_uri, client_id, public_uri)
