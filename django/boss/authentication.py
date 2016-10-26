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

from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication as DRFTokenAuthentication
from oidc_auth.util import cache
from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings
from bossoidc.models import Keycloak as KeycloakModel
from bossutils.keycloak import KeyCloakClient

DRF_KC_TIMEOUT = getattr(django_settings, 'DRF_KC_TIMEOUT', 60 * 5) # 5 Minutes

class TokenAuthentication(DRFTokenAuthentication):
    """Add an extra check to DRF Authentication to make sure the user account is active in keycloak."""
    def authenticate_credentials(self, key):
        user, token = super(TokenAuthentication, self).authenticate_credentials(key)

        try:
            kc_user = KeycloakModel.objects.get(user = user)

            if self.user_exist(kc_user.uid):
                return (user, token) # regular return for authenticate_credentials()
            else:
                # Disable the user in Django to shortcut the Keycloak lookup
                user.is_active = False
                user.save()

                raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))
        except KeycloakModel.DoesNotExist:
            # Regular Django user account
            return (user, token)

    @cache(ttl=DRF_KC_TIMEOUT)
    def user_exists(self, uid):
        """Cache the results of looking up the user in Keycloak"""
        with KeyCloakClient('BOSS') as kc:
            return kc.user_exist(uid)
