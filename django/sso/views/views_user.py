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
from functools import wraps

from django.conf import settings as django_settings

from rest_framework.views import APIView
from rest_framework.response import Response

from bosscore.error import BossKeycloakError, BossHTTPError, ErrorCodes
from bosscore.models import BossRole
from bosscore.serializers import UserSerializer, BossRoleSerializer
from bosscore.privileges import check_role, BossPrivilegeManager

from bossutils.keycloak import KeyCloakClient, KeyCloakError
from bossutils.logger import bossLogger

LOG = bossLogger()

LOCAL_KEYCLOAK_TESTING = getattr(django_settings, 'LOCAL_KEYCLOAK_TESTING', False)
KEYCLOAK_ADMIN_USER = getattr(django_settings, 'KEYCLOAK_ADMIN_USER', '')
KEYCLOAK_ADMIN_PASSWORD = getattr(django_settings, 'KEYCLOAK_ADMIN_PASSWORD', '')

####
## Should there be a hard coded list of valid roles, or shoulda all methods defer
## to Keycloak to make the check that the role is valid. Basically, do we expect
## for different applications to have their own roles?
####
VALID_ROLES = ('admin', 'user-manager', 'resource-manager')

def validate_role(arg=3, kwarg="role_name"):
    """ Validate the role / role_name function argument
        Args:
            kwarg (string): The index into the kwargs dictionary of keyword arguments

        Note: either arg or kwarg should be specified, based on the argument to check
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = args[arg] if len(args) > arg else kwargs.get(kwarg)
            if role is not None and role not in VALID_ROLES:
                return BossHTTPError("Invalid role name {}".format(role), ErrorCodes.INVALID_ROLE)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def filter_roles(roles):
    return [r for r in roles if r in VALID_ROLES]

def check_for_admin(user):
    bpm = BossPrivilegeManager(user)
    if not bpm.has_role('admin'):
        return BossHTTPError(str(user) + " does not have the required role 'admin'", ErrorCodes.MISSING_ROLE)
    else:
        return None

def check_for_user_manager(user):
    bpm = BossPrivilegeManager(user)
    if not bpm.has_role('user-manager') and not bpm.has_role('admin'):
        return BossHTTPError(str(user) + " does not have the required role 'user-manager' or 'admin'", ErrorCodes.MISSING_ROLE)
    else:
        return None

class KeyCloakClientMixin:
    """
    Mixin for that returns a logged in KeyCloakClient if LOCAL_KEYCLOAK_TESTING
    set in the Django settings.
    """

    def get_keycloak_client(self):
        """
        Get the KeyCloak client.

        If LOCAL_KEYCLOAK_TESTING set in the Django settings, logs in using to the
        local test KeyCloak server.

        Returns:
            (KeyCloakClient)
        """
        if LOCAL_KEYCLOAK_TESTING:
            kc = KeyCloakClient('BOSS', url_base='http://localhost:8080/auth', https=False)
            kc.login(
                username=KEYCLOAK_ADMIN_USER,
                password=KEYCLOAK_ADMIN_PASSWORD,
                client_id='admin-cli',
                login_realm='master')
        else:
            kc = KeyCloakClient('BOSS')

        return kc


class BossUser(APIView, KeyCloakClientMixin):
    """
    View to manage users
    """

    def get(self, request, user_name=None):
        """
        Get information about a user

        Args:
           request: Django rest framework request
           user_name: User name to get information about

        Returns:
            JSON dictionary of user data
        """
        try:
            with self.get_keycloak_client() as kc:
                if user_name is None: # Get all users
                    search = request.GET.get('search')
                    response = kc.get_all_users(search)
                    return Response(response, status=200)
                else:
                    response = kc.get_userdata(user_name)
                    roles = kc.get_realm_roles(user_name)
                    response["realmRoles"] = filter_roles([r['name'] for r in roles])
                    return Response(response, status=200)
        except KeyCloakError:
            msg = "Error getting user '{}' from Keycloak".format(user_name)
            return BossKeycloakError(msg)

    @check_role("user-manager")
    def post(self, request, user_name):
        """
        Create a new user

        Args:
            request: Django rest framework request
            user_name: User name of the user to create

        Returns:
            None

        Note: User's data is passed as json data in the request
        """
        user_data = request.data.copy()

        # Keep track of what has been created, so in the catch block we can
        # delete them when there is an error in another step of create user
        user_created = False

        try:
            with self.get_keycloak_client() as kc:
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
                user_created = True

                data = {
                    "type": "password",
                    "temporary": False,
                    "value": user_data.get('password')
                }
                kc.reset_password(user_name, data)

                return Response(status=201)
        except KeyCloakError:
            # cleanup created objects
            if True in [user_created]:
                try:
                    with self.get_keycloak_client() as kc:
                        try:
                            if user_created:
                                kc.delete_user(user_name)
                        except:
                            LOG.exception("Error deleting user '{}'".format(user_name))
                except:
                    LOG.exception("Error communicating with Keycloak to delete created user and primary group")

            msg = "Error addng user '{}' to Keycloak".format(user_name)
            return BossKeycloakError(msg)

    @check_role("admin")
    def delete(self, request, user_name):
        """
        Delete a user

        Args:
            request: Django rest framework request
            user_name: User name of user to delete

        Returns:
            None
        """
        # DP TODO: verify user_name is not an admin
        if user_name == 'bossadmin':
            msg = "Cannot delete user bossadmin from Keycloak".format(user_name)
            return BossKeycloakError(msg)
        else:
            try:
                with self.get_keycloak_client() as kc:
                    kc.delete_user(user_name)

                return Response(status=204)
            except KeyCloakError:
                msg = "Error deleting user '{}' from Keycloak".format(user_name)
                return BossKeycloakError(msg)

class BossUserRole(APIView, KeyCloakClientMixin):
    """
    View to assign role to users
    """

    @validate_role()
    def get(self, request, user_name=None, role_name=None):
        """
        Multi-function method
        1) if user_name and role_name is None, return all roles assigned to 
            logged-in user
        2) If role_name is None but username is specified return all roles 
            assigned to the specified user
        3) If role_name and username specfied, return True/False if the user
            is assigned the given role

        Args:
           request: Django rest framework request
           user_name: User name of the user to check
           role_name: Name of the role to check, or None to return all roles

        Returns:
            True if the user has the role or a list of all assigned roles
        """
        try:
            with self.get_keycloak_client() as kc:
                signed_in_user = request.GET.get('user', str(request.user))

                if user_name is None:
                    user_name = signed_in_user
                else:
                    resp = check_for_user_manager(signed_in_user)
                    if resp is not None:
                        return resp
                
                resp = kc.get_realm_roles(user_name)
                roles = [r['name'] for r in resp]
                roles = filter_roles(roles)

                if role_name is None:
                    return Response(roles, status=200)
                else:
                    exists = role_name in roles
                    return Response(exists, status=200)

        except KeyCloakError:
            msg = "Error getting user '{}' role's from Keycloak".format(user_name)
            return BossKeycloakError(msg)

    @check_role("user-manager")
    @validate_role()
    def post(self, request, user_name, role_name):
        """
        Assign a role to a user

        Args:
            request: Django rest framework request
            user_name: User name of user to assign role to
            role_name : Role name of role to assign to user

        Returns:
            None
        """
        # DP NOTE: admin role has to be assigned manually in Keycloak
        if role_name == 'admin':
            return BossHTTPError("Cannot assign 'admin' role", ErrorCodes.INVALID_ROLE)

        # DP NOTE: user-manager role can only be modified by an admin
        if role_name == 'user-manager':
            resp = check_for_admin(request.user)
            if resp is not None:
                return resp

        try:
            with self.get_keycloak_client() as kc:
                response = kc.map_role_to_user(user_name, role_name)
                return Response(status=201)

        except KeyCloakError:
            msg = "Unable to map role '{}' to user '{}' in Keycloak".format(role_name, user_name)
            return BossKeycloakError(msg)

    @check_role("user-manager")
    @validate_role()
    def delete(self, request, user_name, role_name):
        """
        Unasign a role from a user

        Args:
            request: Django rest framework request
            user_name: User name of user to unassign role from
            role_name : Role name of role to unassign from user

        Returns:
            None
        """
        # DP NOTE: admin role has to be removed manually in Keycloak
        if role_name == 'admin':
            return BossHTTPError("Cannot remove 'admin' role", ErrorCodes.INVALID_ROLE)

        # DP NOTE: user-manager role can only be modified by an admin
        if role_name == 'user-manager':
            resp = check_for_admin(request.user)
            if resp is not None:
                return resp

        try:
            with self.get_keycloak_client() as kc:
                response = kc.remove_role_from_user(user_name, role_name)
                return Response(status=204)

        except KeyCloakError:
            msg = "Unable to remove role '{}' from user '{}' in Keycloak".format(role_name, user_name)
            return BossKeycloakError(msg)
