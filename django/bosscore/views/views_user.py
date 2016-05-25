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

from ..error import BossHTTPError
from ..serializers import GroupSerializer, UserSerializer

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
            user = User.objects.get(name=user_name)
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
        user, created = User.objects.get_or_create(name=user_name)
        if not created:
            return BossHTTPError(404, "A user  with name {} already exist".format(user_name), 30000)
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

            User.objects.get(name=user_name).delete()
            return Response(status=200)

        except Group.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)

class BossUserRole(APIView):
    """
    View to assign role to users
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
            user = User.objects.get(name=user_name)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=200)

        except User.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)

    def post(self, request, user_name,roles):
        """
        Create a new user if the user does not exist
        Args:
            request: Django rest framework request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        try:
            user = User.objects.get(name=user_name)
            print (roles)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=200)

        except User.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)

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

            User.objects.get(name=user_name).delete()
            return Response(status=200)

        except Group.DoesNotExist:
            return BossHTTPError(404, "A user  with name {} is not found".format(user_name), 30000)

