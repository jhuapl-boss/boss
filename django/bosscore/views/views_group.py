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
from bosscore.serializers import GroupSerializer, UserSerializer


class BossGroupMember(APIView):
    """
    View to add a user to a group

    """

    def get(self, request, group_name, user_name=None):
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
            group = Group.objects.get(name=group_name)
            if user_name:
                # Check the membership status for a user
                usr = User.objects.get(username=user_name)
                data = group.user_set.filter(id=usr.id).exists()
                return Response(data, status=200)
            else:
                # Return all the users in the group
                # TODO (pmanava1) - Check if the user has the role to do this
                users = group.user_set.all()
                serializer = UserSerializer(users, many=True)
                return Response(serializer.data, status=200)

        except Group.DoesNotExist:
            return BossHTTPError(404, "A group  with name {} is not found".format(group_name), 30000)
        except User.DoesNotExist:
            return BossHTTPError(404, "User {} not found".format(user_name), 30000)

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
            return BossHTTPError(404, "A group  with name {} is not found".format(group_name), 30000)
        except User.DoesNotExist:
            return BossHTTPError(404, "User {} not found".format(user_name), 30000)

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
            return BossHTTPError(404, "A group  with name {} is not found".format(group_name), 30000)
        except User.DoesNotExist:
            return BossHTTPError(404, "User {} not found".format(user_name), 30000)


class BossGroup(APIView):
    """
    View to manage group memberships
    """
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


    def post(self,request,group_name):
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
            return BossHTTPError(404, "A group  with name {} already exist".format(group_name), 30000)
        return Response(status=201)

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
            return BossHTTPError(404, "A group  with name {} is not found".format(group_name), 30000)
