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
from django.contrib.contenttypes.models import ContentType

from guardian.shortcuts import assign_perm, get_perms, remove_perm, get_perms_for_model
from .error import BossHTTPError, ErrorCodes, BossError
from bosscore.models import BossGroup

def check_is_member_or_maintainer(user, group_name):
    """
    Check if a user is a member or maintainer of the a group
    Args:
        user: User_name
        group_name: Group_name

    Returns:

    """
    try:
        group = Group.objects.get(name = group_name)
        bgroup = BossGroup.objects.get(group=group)
        if user.has_perm("maintain_group", bgroup) or group.user_set.filter(id=user.id).exists():
            return True
        else:
            return False
    except (Group.DoesNotExist , BossGroup.DoesNotExist) as e:
        return BossError("{} does not exist".format(group_name), ErrorCodes.RESOURCE_NOT_FOUND)


class BossPermissionManager:

    @staticmethod
    def is_in_group(user, group_name):
        """
        Takes a user and a group name, and returns `True` if the user is in that group.
        """
        return Group.objects.get(name=group_name).user_set.filter(id=user.id).exists()


    @staticmethod
    def add_permissions_primary_group(user, obj):
        """
        Grant  all permissions to the object for the user's primary group
        Args:
            user: Current user
            obj: Object that we are assigning permission for

        Returns:
            None

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
        assign_perm('assign_group', user_primary_group, obj)
        assign_perm('remove_group', user_primary_group, obj)
        if ct.model == 'channel':
            assign_perm('add_volumetric_data', user_primary_group, obj)
            assign_perm('read_volumetric_data', user_primary_group, obj)
            assign_perm('delete_volumetric_data', user_primary_group, obj)



    @staticmethod
    def add_permissions_group(group_name, obj, perm_list):
        """
        Grant permissions to the object for a group
        Args:
            group_name: Name of an existing group
            obj: Resource
            perm_list: List of permissions to be assigned for the resource and group

        Returns:
            None

        """
        # Validate the list of permission
        ct = ContentType.objects.get_for_model(obj)
        perms = [perm.codename for perm in get_perms_for_model(ct.model_class())]
        if not set(perm_list).issubset(perms):
            raise BossError("Invalid permissions {} in the request".format(perm_list), ErrorCodes.INVALID_POST_ARGUMENT)

        # Get the type of model
        group = Group.objects.get(name=group_name)
        for perm in perm_list:
            assign_perm(perm, group, obj)

    @staticmethod
    def get_permissions_group(group_name, obj):
        """
        Return the permissions for a group
        Args:
            group_name : Name of existing group
            obj: Object that we are getting permission for

        Returns:
            List of permissions

        """
        # Get the type of model
        group = Group.objects.get(name=group_name)
        return get_perms(group,obj)

    @staticmethod
    def delete_permissions_group(group_name, obj, perm_list):
        """
        Delete permissions for a resource
        Args:
            group_name : Name of existing group
            obj: Object that we are getting permission for
            perm_list : List of permissions to be deleted

        Returns:

        """
        # Get the type of model
        group = Group.objects.get(name=group_name)
        for perm in perm_list:
            remove_perm(perm, group, obj)

    @staticmethod
    def delete_all_permissions_group(group_name, obj):
        """
        Delete  all permissions for a resource
        Args:
            group_name : Name of existing group
            obj: Object that we are getting permission for
            perm_list : List of permissions to be deleted

        Returns:

        """
        # Get the type of model
        group = Group.objects.get(name=group_name)
        perm_list = get_perms(group, obj)
        for perm in perm_list:
            remove_perm(perm, group, obj)

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
            admin_group, created = Group.objects.get_or_create(name="admin")
            if created:
                admin_user = User.objects.get(username='bossadmin')
                bgroup = BossGroup.objects.create(group=admin_group, creator=admin_user)
                
            ct = ContentType.objects.get_for_model(obj)
            assign_perm('read', admin_group, obj)
            assign_perm('add', admin_group, obj)
            assign_perm('update', admin_group, obj)
            assign_perm('delete', admin_group, obj)
            assign_perm('assign_group', admin_group, obj)
            assign_perm('remove_group', admin_group, obj)
            if ct.model == 'channel':
                assign_perm('add_volumetric_data', admin_group, obj)
                assign_perm('read_volumetric_data', admin_group, obj)
                assign_perm('delete_volumetric_data', admin_group, obj)

        except Group.DoesNotExist:
            raise BossError("Cannot assign permissions to the admin group because the group does not exist",
                            ErrorCodes.GROUP_NOT_FOUND)

    @staticmethod
    def check_resource_permissions(user, obj, method_type):
        """
        Check user permissions for a resource object
        Args:
            user: User name
            obj: Obj
            method_type: Method type specified in the request

        Returns:
            bool. True if the user has the permission on the resource

        """
        if method_type == 'GET':
            permission = 'read'
        elif method_type == 'POST':
            permission = 'add'
        elif method_type == 'PUT':
            permission = 'update'
        elif method_type == 'DELETE':
            permission = 'delete'
        else:
            raise BossError("Unable to get permissions for this request", ErrorCodes.INVALID_POST_ARGUMENT)

        if permission in get_perms(user, obj):
            return True
        else:
            return False

    @staticmethod
    def check_data_permissions(user, obj, method_type):
        """
        Check user permissions for a data
        Args:
            user: User name
            obj: resource
            method_type: Method type specified in the post

        Returns:
            bool. True if the user has the permission on the resource

        """
        if method_type == 'GET':
            permission = 'read_volumetric_data'
        elif method_type == 'POST' or method_type == 'PUT':
            permission = 'add_volumetric_data'
        elif method_type == 'DELETE':
            permission = 'delete_volumetric_data'
        else:
            raise BossError("Unable to get permissions for this request", ErrorCodes.INVALID_POST_ARGUMENT)

        if permission in get_perms(user, obj):
            return True
        else:
            return False

    @staticmethod
    def check_object_permissions(user, obj, method_type):
        """
        Check permissions for object services (currently only the reserve service uses this)
        Args:
            user: User name
            obj: resource
            method_type: Mothod type specified in the post

        Returns:
            bool. True if the user has the permission on the resource

        """
        if method_type == 'GET':
            permission = 'add_volumetric_data'
        else:
            raise BossError("Invalid method type. This query only supports a GET", ErrorCodes.INVALID_POST_ARGUMENT)

        if permission in get_perms(user, obj):
            return True
        else:
            return False