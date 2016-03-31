from django.contrib.auth.models import Group

from guardian.shortcuts import assign_perm,get_perms
from .error import BossError, BossHTTPError



class BossPermissionManager:

    @staticmethod
    def is_in_group(user, group_name):
        """
        Takes a user and a group name, and returns `True` if the user is in that group.
        """
        return Group.objects.get(name=group_name).user_set.filter(id=user.id).exists()

    @staticmethod
    def add_permissions_primary_group(user,obj,obj_name):
        """
        Grant permissions to the object for the user's primary group
        Args:
            user: Current user
            obj: Object that we are assigning permission for
            obj_name :

        Returns:

        """
        group_name = user.username + "-primary"
        user_primary_group = Group.objects.get_or_create(name=group_name)[0]
        user.groups.add(user_primary_group.pk)

        assign_perm('view_'+obj_name, user_primary_group, obj)
        assign_perm('add_'+obj_name, user_primary_group, obj)
        assign_perm('change_'+obj_name, user_primary_group, obj)
        assign_perm('delete_'+obj_name, user_primary_group, obj)

    @staticmethod
    def check_permissions_object(user,obj,method_type,obj_name):
        """
        Args:
            user:
            obj:
            permission:
            obj_name:

        Returns:

        """
        if method_type == 'GET':
            permission = 'view_' + obj_name
        elif method_type == 'POST':
            permission = 'add_' + obj_name
        elif method_type == 'PUT':
            permission = 'change_' + obj_name
        elif method_type == 'DELETE':
            permission = 'delete_' + obj_name
        else:
            return BossHTTPError(404, "Unable to get permissions for this request".format(method_type), 30000)

        if permission in get_perms(user,obj):
            return True
        else:
            return False

