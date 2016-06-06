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

from django.contrib.auth.models import Group, User

from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse

from bosscore.error import BossHTTPError
from bosscore.models import BossRole
from bosscore.serializers import GroupSerializer, UserSerializer, BossRoleSerializer
from bosscore.privileges import BossPrivilegeManager

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
            user = User.objects.get(username=user_name)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=200)

        except User.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)

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
        user, created = User.objects.get_or_create(username=user_name, **user_data)

        if not created:
            return BossHTTPError(404, "A user with username {} already exist".format(user_name), 30000)
        else:
            # create the user's primary group
            group_name = user_name + PRIMARY_GROUP
            primary_group, created = Group.objects.get_or_create(name=group_name)
            if not created:
                # delete the user and return an error
                User.objects.get(username=user_name).delete()
                return BossHTTPError(404, "The primary group for this username already exists".format(group_name),
                                     30000)
            else:
                # TODO (pmanava1) - If the public group does not exist,create it . This should be
                # created in setup instead
                public_group, created = Group.objects.get_or_create(name=PUBLIC_GROUP)
                public_group.user_set.add(user)

        return Response(status=201)

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
            Group.objects.get(name=user_name + PRIMARY_GROUP).delete()
            User.objects.get(username=user_name).delete()
            return Response(status=200)

        except User.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)
        except Group.DoesNotExist:
            return BossHTTPError(404, "Could not find the primary group for the user".format(user_name), 30000)

class BossUserGroups(APIView):
    """
    View to list a users group
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
            user = User.objects.get(username=user_name)
            groups = user.groups.all()
            serializer = GroupSerializer(groups, many=True)
            return Response(serializer.data, status=200)

        except User.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)


class BossUserRole(APIView):
    """
    View to assign role to users
    """
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
            if role_name == None:
                # List all roles that the user has
                bpm = BossPrivilegeManager(user_name)
                return bpm.get_user_roles()

            if role_name not in ['admin', 'user-manager', 'resource-manager']:
                return BossHTTPError(404, "Invalid role name {}".format(role_name), 30000)

            user = User.objects.get(username=user_name)
            status = BossRole.objects.filter(user=user, role=role_name).exists()
            return Response(status, status=200)
        except User.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)

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
            user = User.objects.get(username=user_name)
            if role_name not in ['admin', 'user-manager', 'resource-manager']:
                return BossHTTPError(404, "Invalid role name {}".format(role_name), 30000)

            data = {'user': user.pk, 'role': role_name}
            serializer = BossRoleSerializer(data=data)
            if serializer.is_valid():
                serializer.save()

            return Response(serializer.data, status=200)

        except User.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)

    def delete(self, request, user_name, role_name):
        """
        Delete a user
        Args:
            request: Django rest framework request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        try:

            user = User.objects.get(username=user_name)
            if role_name not in ['admin', 'user-manager', 'resource-manager']:
                return BossHTTPError(404, "Invalid role name {}".format(role_name), 30000)
            role = BossRole.objects.get(user=user, role=role_name)
            role.delete()

            return Response(status=204)

        except User.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)
        except BossRole.DoesNotExist:
            return BossHTTPError(404, "The user {} does not have the role {} ".format(user_name, role_name), 30000)
