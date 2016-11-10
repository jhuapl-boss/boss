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

from guardian.shortcuts import get_objects_for_user, get_perms_for_model, assign_perm, get_users_with_perms, \
    remove_perm, get_objects_for_group, get_perms


from bosscore.privileges import check_role, BossPrivilegeManager
from bosscore.error import BossHTTPError, ErrorCodes, BossGroupNotFoundError, BossUserNotFoundError
from bosscore.serializers import GroupSerializer, UserSerializer

from bosscore.models import BossGroup, Collection, Experiment, Channel


class BossGroupMember(APIView):
    """
    View to add a user to a group

    """

    @check_role("resource-manager")
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
            bgroup = BossGroup.objects.get(group=group)

            # Check for permissions. The logged in user has to be a member or group maintainer
            if not request.user.has_perm("maintain_group", bgroup) and \
                    not group.user_set.filter(id=request.user.id).exists():
                return BossHTTPError('The user {} is not a member or maintainer of the group {} '
                                     .format(request.user.username, group_name),
                                     ErrorCodes.MISSING_PERMISSION)
            if user_name is None:
                # Return all users for the group
                list_users = group.user_set.all().values_list('username', flat=True)
                list_users = [name for name in list_users]
                data = {"members": list_users}
            else:
                # Both group name and user name are specified. Return the membership status for the user
                group = Group.objects.get(name=group_name)
                usr = User.objects.get(username=user_name)
                status = group.user_set.filter(id=usr.id).exists()
                data = {"result": status}

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
            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)

            # Check the users permissions.
            if request.user.has_perm("maintain_group", bgroup):
                usr = User.objects.get(username=user_name)
                bgroup.group.user_set.add(usr)
                return HttpResponse(status=204)
            else:
                return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                     .format(request.user.username, 'maintain_group', group_name),
                                     ErrorCodes.MISSING_PERMISSION)

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

            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)

            # Check the users permissions.
            if request.user.has_perm("maintain_group", bgroup):
                usr = User.objects.get(username=user_name)
                bgroup.group.user_set.remove(usr)
                return HttpResponse(status=204)
            else:
                return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                     .format(request.user.username, 'maintain_group', group_name),
                                     ErrorCodes.MISSING_PERMISSION)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)


class BossGroupMaintainer(APIView):
    """
    View to add a user to a group

    """

    @check_role("resource-manager")
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
            bgroup = BossGroup.objects.get(group=group)

            # Check for permissions. The logged in user has to be a member or group maintainer
            if not request.user.has_perm("maintain_group", bgroup) and \
                    not group.user_set.filter(id=request.user.id).exists():
                return BossHTTPError('The user {} is not a member or maintainer of the group {} '
                                     .format(request.user.username, group_name),
                                     ErrorCodes.MISSING_PERMISSION)
            if user_name is None:

                # Return all maintainers for the group
                list_maintainers = get_users_with_perms(bgroup)
                maintainers = [user.username for user in list_maintainers]
                data = {"maintainers": maintainers}
            else:
                # Both group name and user name are specified. Return the membership status for the user
                usr = User.objects.get(username=user_name)
                status = usr.has_perm("maintain_group", bgroup)
                data = {"result": status}

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
            if user_name is None:
                return BossHTTPError('Missing username in post.', ErrorCodes.INVALID_URL)

            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)

            # Check the users permissions.
            if request.user.has_perm("maintain_group", bgroup):
                usr = User.objects.get(username=user_name)

                # assign permissions to the creator of the group
                group_perms = [perm.codename for perm in get_perms_for_model(BossGroup)]
                for permission in group_perms:
                    assign_perm(permission, usr, bgroup)
                return HttpResponse(status=204)

            else:
                return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                     .format(request.user.username, 'maintain_group', group_name),
                                     ErrorCodes.MISSING_PERMISSION)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)

    @check_role("resource-manager")
    def delete(self, request, group_name, user_name):
        """
        Removes a maintainer form the group
        Args:
            request: Django rest framework request
            group_name:Group name from the request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        try:
            if user_name is None:
                return BossHTTPError('Missing username parameter in post.', ErrorCodes.INVALID_URL)

            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)

            # Check the users permissions.
            if request.user.has_perm("maintain_group", bgroup):
                usr = User.objects.get(username=user_name)
                status = usr.has_perm('maintain_group', bgroup)

                if status is False:
                    return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                         .format(usr.username, 'maintain_group', group_name),
                                         ErrorCodes.MISSING_PERMISSION)
                else:
                    remove_perm('maintain_group', usr, bgroup)

                return HttpResponse(status=204)
            else:
                return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                     .format(request.user.username, 'maintain_group', group_name),
                                     ErrorCodes.MISSING_PERMISSION)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)


class BossUserGroup(APIView):
    """
    View to manage group memberships
    """

    @check_role("resource-manager")
    def get(self, request, group_name=None):
        """
        Get all group s
        Args:
           request: Django rest framework request
           group_name: Group name from the request

       Returns:
            Group if the group exists
        """
        if group_name is not None:
            try:
                group = Group.objects.get(name=group_name)
                bgroup = BossGroup.objects.get(group=group)
                data = {"name": group.name, "owner": bgroup.creator.username}
                resources = []

                # get permission sets for models
                col_perms = [perm.codename for perm in get_perms_for_model(Collection)]
                exp_perms = [perm.codename for perm in get_perms_for_model(Experiment)]
                channel_perms = [perm.codename for perm in get_perms_for_model(Channel)]

                # get objects for the group
                col_list = get_objects_for_group(group, perms=col_perms, klass=Collection, any_perm=True)
                exp_list = get_objects_for_group(group, perms=exp_perms, klass=Experiment, any_perm=True)
                ch_list = get_objects_for_group(group, perms=channel_perms, klass=Channel, any_perm=True)

                for col in col_list:
                    obj = {'collection': col.name}
                    resources.append(obj)

                for exp in exp_list:
                    obj = {'collection': exp.collection.name, 'experiment': exp.name}
                    resources.append(obj)

                for ch in ch_list:
                    obj = {'collection': ch.experiment.collection.name, 'experiment': ch.experiment.name,
                           'channel': ch.name}
                    resources.append(obj)

                data['resources'] = resources
                return Response(data, status=200)
            except Group.DoesNotExist:
                return BossGroupNotFoundError(group_name)
        else:
            # Get all the groups that the logged in user is a member of
            list_member_groups = request.user.groups.values_list('name', flat=True)
            member_groups = [name for name in list_member_groups]

            # Get all groups that the user has maintainer permissions on
            group_perms = [perm.codename for perm in get_perms_for_model(BossGroup)]
            list_maintainer_groups = get_objects_for_user(request.user, group_perms, klass=BossGroup, any_perm=True)
            maintainer_groups = [bgroup.group.name for bgroup in list_maintainer_groups]

            if 'filter' in request.query_params and request.query_params['filter'] == 'member':
                data = {'groups': member_groups}
                return Response(data, status=200)
            elif 'filter' in request.query_params and request.query_params['filter'] == 'maintainer':
                data = {'groups': maintainer_groups}
                return Response(data, status=200)
            elif 'filter' not in request.query_params:
                all_groups = list(set(member_groups).union(maintainer_groups))
                data = {'groups': all_groups}
            else:
                return BossHTTPError('Unrecogizes value {} in filter. Valid parameters are member or maintainer.',
                                     ErrorCodes.UNABLE_TO_VALIDATE)
            return Response(data, status=200)

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
        bgroup = BossGroup.objects.create(group=group, creator=request.user)

        # assign permissions to the creator of the group
        group_perms = [perm.codename for perm in get_perms_for_model(BossGroup)]
        for permission in group_perms:
            assign_perm(permission, request.user, bgroup)

        # add the creator to the group
        bgroup.group.user_set.add(request.user)
        return Response(status=201)

    @check_role("resource-manager")
    def delete(self, request, group_name):
        """
        Delete a group. The user has to be an admin or the creator of the group
        Args:
            request: Django rest framework request
            group_name: Group name from the request

        Returns:
            Http status of the request

        """
        try:

            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)
            bpm = BossPrivilegeManager(request.user)
            if request.user == bgroup.creator or bpm.has_role('admin'):
                group.delete()
                return Response(status=204)
            else:
                return BossHTTPError('Groups can only be deleted by the creator or administrator',
                                     ErrorCodes.MISSING_ROLE)
        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
