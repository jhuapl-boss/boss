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

from bosscore.privileges import check_role
from bosscore.error import BossHTTPError, ErrorCodes, BossGroupNotFoundError, BossUserNotFoundError
from bosscore.serializers import GroupSerializer, UserSerializer


class BossGroupMemberList(APIView):
    """
    Class to get group membership information

    """

    @check_role("resource-manager")
    def get(self, request):
        """
        Gets the membership status of a user for a group
        Args:
           request: Django rest framework request
           group_name: Group name from the request
           user_name: User name from the request

       Returns:
           bool : True if the user is a member of the group

        """
        if 'groupname' in request.query_params:
            groupname = request.query_params['groupname']
        else:
            groupname = None

        if 'username' in request.query_params:
            username = request.query_params['username']
        else:
            username = None


        try:

            if username is None and groupname is None:
                #  Both the user-name and group name is not specified. Return all groups for the logged in user
                list_groups = request.user.groups.values_list('name', flat=True)
                list_groups = [name for name in list_groups]
                data = {"groups": list_groups}
            elif username is not None and groupname is None:
                # username without groupname. Return all groups for this user
                user = User.objects.get(username=username)
                list_groups = user.groups.values_list('name', flat=True)
                list_groups = [name for name in list_groups]
                data = {"groups": list_groups}
            elif username is None and groupname is not None:
                # The group name is specified without the username. Return a list of all users in the group
                group = Group.objects.get(name=groupname)
                list_users = group.user_set.all().values_list('username', flat=True)
                list_users = [name for name in list_users]
                data = {"group-members": list_users}
            else:
                # Both group name and user name are specified. Return the membership status for the user
                group = Group.objects.get(name=groupname)
                usr = User.objects.get(username=username)
                data = group.user_set.filter(id=usr.id).exists()

            return Response(data, status=200)
        except Group.DoesNotExist:
            return BossGroupNotFoundError(groupname)
        except User.DoesNotExist:
            return BossUserNotFoundError(username)

class BossGroupMember(APIView):
    """
    View to add a user to a group

    """

    @check_role("resource-manager")
    def get(self, request, group_name, user_name):
        """
        Gets the membership status of a user for a group
        Args:
           request: Django rest framework request
           group_name: Group name from the request
           user_name: User name from the request

       Returns:
           bool : True if the user is a member of the group

        """
        try:
            # Both group name and user name are specified. Return the membership status for the user
            group = Group.objects.get(name=group_name)
            usr = User.objects.get(username=user_name)
            data = group.user_set.filter(id=usr.id).exists()

            return Response(data, status=200)
        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)

    @check_role("resource-manager")
    def post(self, request, group_name, user_name):
        """
        Adds a user to a group
        Args:
            request: Django rest framework request
            group_name: Group name from the request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        try:
            usr = User.objects.get(username=user_name)
            Group.objects.get(name=group_name).user_set.add(usr)
            return HttpResponse(status=201)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)

    @check_role("resource-manager")
    def delete(self, request, group_name, user_name):
        """
        Removes a user from a group
        Args:
            request: Django rest framework request
            group_name:Group name from the request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        try:
            usr = User.objects.get(username=user_name)
            Group.objects.get(name=group_name).user_set.remove(usr)
            return HttpResponse(status=204)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)


class BossGroup(APIView):
    """
    View to manage group memberships
    """

    @check_role("resource-manager")
    def get(self, request, group_name):
        """
        Get the group information
        Args:
           request: Django rest framework request
           group_name: Group name from the request

       Returns:
            Group if the group exists
        """
        exists = Group.objects.filter(name=group_name).exists()
        return Response(exists, status=200)

    @check_role("resource-manager")
    def post(self, request, group_name):
        """
        Create a new group is the group does not exist
        Args:
            request: Django rest framework request
            group_name: Group name from the request

        Returns:
            Http status of the request

        """
        group, created = Group.objects.get_or_create(name=group_name)
        if not created:
            return BossHTTPError("A group  with name {} already exist".format(group_name), ErrorCodes.GROUP_EXISTS)
        return Response(status=201)

    @check_role("resource-manager")
    def delete(self, request, group_name):
        """
        Delete a group
        Args:
            request: Django rest framework request
            group_name: Group name from the request

        Returns:
            Http status of the request

        """
        try:
            Group.objects.get(name=group_name).delete()
            return Response(status=204)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
