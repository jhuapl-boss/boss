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

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType

from guardian.shortcuts import assign_perm, get_perms
from .error import BossHTTPError


class BossPermissionManager:

    @staticmethod
    def is_in_group(user, group_name):
        """
        Takes a user and a group name, and returns `True` if the user is in that group.
        """
        return Group.objects.get(name=group_name).user_set.filter(id=user.id).exists()

    @staticmethod
    def add_permissions_user(user, obj):
        """
        Grant permissions to the object for the user's primary group
        Args:
            user: Current user
            obj: Object that we are assigning permission for
            obj_name :

        Returns:

        """
        # Get the type of model
        ct = ContentType.objects.get_for_model(obj)
        group_name = user.username + "-primary"
        user_primary_group = Group.objects.get_or_create(name=group_name)[0]
        user.groups.add(user_primary_group.pk)

        assign_perm('read', user_primary_group, obj)
        assign_perm('add', user_primary_group, obj)
        assign_perm('update', user_primary_group, obj)
        assign_perm('delete', user_primary_group, obj)

    @staticmethod
    def add_permissions_primary_group(user, obj):
        """
        Grant permissions to the object for the user's primary group
        Args:
            user: Current user
            obj: Object that we are assigning permission for
            obj_name :

        Returns:

        """
        # Get the type of model
        ct = ContentType.objects.get_for_model(obj)
        group_name = user.username + "-primary"
        user_primary_group = Group.objects.get_or_create(name=group_name)[0]
        user.groups.add(user_primary_group.pk)

        assign_perm('read', user_primary_group, obj)
        assign_perm('add', user_primary_group, obj)
        assign_perm('update', user_primary_group, obj)
        assign_perm('delete', user_primary_group, obj)

    @staticmethod
    def add_permissions_admin_group(obj):
        """
        Grant permissions to the admin group for an object
        Args:

            obj: Object that we are assigning permission for

        Returns:
            None
        """
        # Get the type of model
        try:
            admin_group = Group.objects.get(name="admin")[0]
            print (admin_group)
            ct = ContentType.objects.get_for_model(obj)
            assign_perm('read', admin_group, obj)
            assign_perm('add', admin_group, obj)
            assign_perm('update', admin_group, obj)
            assign_perm('delete', admin_group, obj)
        except Group.DoesNotExist:
            BossHTTPError(404, "{Cannot assign permissions to the admin group because the group does not exist}", 30000)

    @staticmethod
    def check_permissions_object(user, obj, method_type, obj_name):
        """
        Args:
            user:
            obj:
            method_type:
            obj_name:

        Returns:

        """
        if method_type == 'GET':
            permission = 'read' + obj_name
        elif method_type == 'POST':
            permission = 'add' + obj_name
        elif method_type == 'PUT':
            permission = 'update' + obj_name
        elif method_type == 'DELETE':
            permission = 'delete' + obj_name
        else:
            return BossHTTPError(404, "Unable to get permissions for this request", 30000)

        if permission in get_perms(user, obj):
            return True
        else:
            return False
