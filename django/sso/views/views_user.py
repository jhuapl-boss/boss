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

import json
from django.contrib.auth.models import Group, User
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse

from bosscore.error import BossHTTPError
from bosscore.models import BossRole
from bosscore.serializers import GroupSerializer, UserSerializer, BossRoleSerializer
from bosscore.privileges import BossPrivilegeManager
from bosscore.privileges import check_role

from bossutils.keycloak import KeyCloakClient
from bossutils.logger import BossLogger

LOG = BossLogger().logger

# GROUP NAMES
PUBLIC_GROUP = 'boss-public'
PRIMARY_GROUP = '-primary'


class BossUser(APIView):
    """
    View to manage users
    """
    def get(self, request, user_name):
        """
        Get the user information
        Args:
           request: Django rest framework request
           user_name: User name from the request

        Returns:
            User if the user exists
        """
        try:
            with KeyCloakClient('BOSS') as kc:
                response = kc.get_userdata(user_name)
                roles = kc.get_realm_roles(user_name)
                response["realmRoles"] = [r['name'] for r in roles]
                return Response(response, status=200)
        except Exception as e:
            msg = "Error getting user '{}' from Keycloak".format(user_name)
            return BossHTTPError.from_exception(e, 404, msg, 30000)

    @check_role("user-manager")
    @transaction.atomic
    def post(self, request, user_name):
        """
        Create a new user if the user does not exist
        Args:
            request: Django rest framework request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        user_data = request.data.copy()

        # Keep track of what has been created, so in the catch block we can
        # delete them when there is an error in another step of create user
        user_created = False

        try:
            with KeyCloakClient('BOSS') as kc:
                # Create the user account, attached to the default groups
                # DP NOTE: email also has to be unique, in the current configuration of Keycloak
                data = {
                    "username": user_name,
                    "firstName": user_data.get('first_name'),
                    "lastName": user_data.get('last_name'),
                    "email": user_data.get('email'),
                    "enabled": True
                }
                data = json.dumps(data)
                response = kc.create_user(data)
                user_create = True

                data = {
                    "type": "password",
                    "temporary": False,
                    "value": user_data.get('password')
                }
                kc.reset_password(user_name, data)

                return Response(response, status=201)
        except Exception as e:
            # cleanup created objects
            if True in [user_created]:
                try:
                    with KeyCloakClient('BOSS') as kc:
                        try:
                            if user_created:
                                kc.delete_user(user_name)
                        except:
                            LOG.exception("Error deleting user '{}'".format(user_name))
                except:
                    LOG.exception("Error communicating with Keycloak to delete created user and primary group")

            msg = "Error addng user '{}' to Keycloak".format(user_name)
            return BossHTTPError.from_exception(e, 404, msg, 30000)

    @check_role("user-manager")
    def delete(self, request, user_name):
        """
        Delete a user
        Args:
            request: Django rest framework request
            user_name: User name from the request
        Returns:
            Http status of the request
        """
        try:
            # Delete from Keycloak
            with KeyCloakClient('BOSS') as kc:
                kc.delete_user(user_name)

            return Response(status=204)
        except Exception as e:
            msg = "Error deleting user '{}' from Keycloak".format(user_name)
            return BossHTTPError.from_exception(e, 404, msg, 30000)



class BossUserRole(APIView):
    """
    View to assign role to users
    """

    @check_role("user-manager")
    def get(self, request, user_name, role_name=None):
        """
        Check if the user has a specific role
        Args:
           request: Django rest framework request
           user_name: User name
           role_name:

        Returns:
            True if the user has the role
        """
        try:
            with KeyCloakClient('BOSS') as kc:
                resp = kc.get_realm_roles(user_name)
                roles = [r['name'] for r in resp]
                # DP TODO: filter roles array to limit to valid roles??

                if role_name is None:
                    return Response(roles, status=200)
                else:
                    valid = ['admin', 'user-manager', 'resource-manager']
                    if role_name not in valid:
                        return BossHTTPError(404, "Invalid role name {}".format(role_name), 30000)

                    exists = role_name in roles
                    return Response(exists, status=200)

        except Exception as e:
            return BossHTTPError(404, "Error getting user's {} roles from keycloak. {}".format(user_name, e), 30000)

    @check_role("user-manager")
    def post(self, request, user_name, role_name):
        """
        Assign a role to a user
        Args:
            request: Django rest framework request
            user_name: User name
            role_name : Role name

        Returns:
            Http status of the request

        """
        try:
            if role_name not in ['admin', 'user-manager', 'resource-manager']:
                return BossHTTPError(404, "Invalid role name {}".format(role_name), 30000)

            with KeyCloakClient('BOSS') as kc:
                response = kc.map_role_to_user(user_name, role_name)
                return Response(serializer.data, status=201)

        except Exception as e:
            return BossHTTPError(404, "Unable to map role {} to user {} in keycloak. {}".format(role_name, user_name, e), 30000)

    @check_role("user-manager")
    def delete(self, request, user_name, role_name):
        """
        Delete a user
        Args:
            request: Django rest framework request
            user_name: User name from the request
            role_name: Role name from the request

        Returns:
            Http status of the request

        """
        try:

            if role_name not in ['admin', 'user-manager', 'resource-manager']:
                return BossHTTPError(404, "Invalid role name {}".format(role_name), 30000)
            with KeyCloakClient('BOSS') as kc:
                response = kc.remove_role_from_user(user_name, role_name)
                return Response(status=204)

        except Exception as e:
            return BossHTTPError(404,
                                 "Unable to remove role {} from user {} in keycloak. {}".format(role_name, user_name, e),
                                 30000)
