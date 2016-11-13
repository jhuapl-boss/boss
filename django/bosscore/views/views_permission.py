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

from django.db import transaction
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from guardian.shortcuts import get_perms_for_model, get_objects_for_group, get_perms

from bosscore.models import Collection, Experiment, Channel, BossGroup
from bosscore.permissions import BossPermissionManager, check_is_member_or_maintainer
from bosscore.error import BossHTTPError, BossError, ErrorCodes, BossResourceNotFoundError,\
    BossGroupNotFoundError, BossPermissionError
from bosscore.privileges import check_role


class ResourceUserPermission(APIView):
    """
    View to assign Permissions to resource instances

    """

    @staticmethod
    def get_object(collection, experiment=None, channel=None):
        """ Return the resource from the request

        Args:
            collection: Collection name from the request
            experiment: Experiment name from the request
            channel: Channel name

        Returns:
            Instance of the resource from the request

        """
        try:
            if collection and experiment and channel:
                # Channel specified
                collection_obj = Collection.objects.get(name=collection)
                experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
                obj = Channel.objects.get(name=channel, experiment=experiment_obj)
                resource_type = 'channel'
            elif collection and experiment:
                # Experiment
                collection_obj = Collection.objects.get(name=collection)
                obj = Experiment.objects.get(name=experiment, collection=collection_obj)
                resource_type = 'experiment'
            elif collection:
                obj = Collection.objects.get(name=collection)
                resource_type = 'collection'
            else:
                return None

            return (obj, resource_type)
        except Collection.DoesNotExist:
            raise BossError("{} does not exist".format(collection), ErrorCodes.RESOURCE_NOT_FOUND)
        except Experiment.DoesNotExist:
            raise BossError("{} does not exist".format(experiment), ErrorCodes.RESOURCE_NOT_FOUND)
        except Channel.DoesNotExist:
            raise BossError("{} does not exist".format(channel), ErrorCodes.RESOURCE_NOT_FOUND)

    @check_role("resource-manager")
    def get(self, request):
        """Return a list of permissions

        Get the list of the permissions for a group on a resource. These determine the access for the users
        in the group on the resource

        Args:
           request: Django Rest framework request

        Returns:
           List of permissions

        """
        try:
            obj_list = []
            group = request.query_params.get('group', None)
            collection = request.query_params.get('collection', None)
            experiment = request.query_params.get('experiment', None)
            channel = request.query_params.get('channel', None)

            # get permission sets for models
            col_perms = [perm.codename for perm in get_perms_for_model(Collection)]
            exp_perms = [perm.codename for perm in get_perms_for_model(Experiment)]
            channel_perms = [perm.codename for perm in get_perms_for_model(Channel)]

            resource_object = self.get_object(collection, experiment, channel)

            if group and resource_object:
                group = Group.objects.get(name=group)
                resource_type = resource_object[1]

                # filtering on both group and resource
                resource = resource_object[0]

                perms = get_perms(group, resource)
                if len(perms) == 0:
                    # Nothing to return
                    data = {'permission-sets': []}
                    return Response(data, status=status.HTTP_200_OK)

                if resource_type == 'collection':
                    obj = {'group': group.name, 'collection': resource.name, 'permissions': perms}
                    obj_list.append(obj)
                    data = {'permission-sets': obj_list}
                elif resource_type == 'experiment':
                    obj = {'group': group.name, 'collection': resource.collection.name, 'experiment': resource.name,
                           'permissions': perms}
                    obj_list.append(obj)
                    data = {'permission-sets': obj_list}
                else:
                    obj = {'group': group.name, 'collection': resource.experiment.collection.name,
                           'experiment': resource.experiment.name, 'channel': resource.name,
                           'permissions': perms}
                    obj_list.append(obj)
                    data = {'permission-sets': obj_list}

            elif resource_object and not group:
                # filtering on resource
                resource = resource_object[0]
                resource_type = resource_object[1]
                list_member_groups = request.user.groups.all()
                for group in list_member_groups:
                    perms = get_perms(group, resource)
                    if resource_type == 'collection' and len(perms) > 0:
                        obj = {'group': group.name, 'collection': resource.name, 'permissions': perms}
                        obj_list.append(obj)
                    elif resource_type == 'experiment' and len(perms) > 0:
                        obj = {'group': group.name, 'collection': resource.collection.name, 'experiment': resource.name,
                               'permissions': perms}
                        obj_list.append(obj)
                    elif resource_type == 'channel' and len(perms) > 0:
                        obj = {'group': group.name, 'collection': resource.experiment.collection.name,
                               'experiment': resource.experiment.name, 'channel': resource.name,
                               'permissions': perms}
                        obj_list.append(obj)
                data = {'permission-sets': obj_list}
            elif group and not resource_object:
                # filtering on group
                group = Group.objects.get(name=group)
                col_list = get_objects_for_group(group, perms=col_perms, klass=Collection, any_perm=True)
                for col in col_list:
                    col_perms = get_perms(group, col)
                    obj = {'group': group.name, 'collection': col.name, 'permissions': col_perms}
                    obj_list.append(obj)

                exp_list = get_objects_for_group(group, perms=exp_perms, klass=Experiment, any_perm=True)
                for exp in exp_list:
                    exp_perms = get_perms(group, exp)
                    obj_list.append({'group': group.name, 'collection': exp.collection.name, 'experiment': exp.name,
                                     'permissions': exp_perms})

                ch_list = get_objects_for_group(group, perms=channel_perms, klass=Channel, any_perm=True)
                for channel in ch_list:
                    channel_perms = get_perms(group, channel)
                    obj_list.append({'group': group.name, 'collection': channel.experiment.collection.name,
                                     'experiment': channel.experiment.name, 'channel': channel.name,
                                     'permissions': channel_perms})

                data = {'permission-sets': obj_list}
            else:
                # no filtering

                list_member_groups = request.user.groups.all()
                for group in list_member_groups:
                    col_list = get_objects_for_group(group, perms=col_perms, klass=Collection, any_perm=True)
                    for col in col_list:
                        col_perms = get_perms(group, col)
                        obj = {'group': group.name, 'collection': col.name, 'permissions': col_perms}
                        obj_list.append(obj)

                    exp_list = get_objects_for_group(group, perms=exp_perms, klass=Experiment, any_perm=True)
                    for exp in exp_list:
                        exp_perms = get_perms(group, exp)
                        obj_list.append({'group': group.name, 'collection': exp.collection.name,
                                         'experiment': exp.name, 'permissions': col_perms})

                    ch_list = get_objects_for_group(group, perms=channel_perms, klass=Channel, any_perm=True)
                    for channel in ch_list:
                        channel_perms = get_perms(group, channel)
                        obj_list.append({'group': group.name, 'collection': channel.experiment.collection.name,
                                         'experiment': channel.experiment.name, 'channel': channel.name,
                                         'permissions': col_perms})

                data = {'permission-sets': obj_list}
            return Response(data, status=status.HTTP_200_OK)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group)
        except Permission.DoesNotExist:
            return BossHTTPError("Invalid permissions in post".format(request.data['permissions']),
                                 ErrorCodes.UNRECOGNIZED_PERMISSION)
        except BossError as err:
            return err.to_http()

    @transaction.atomic
    @check_role("resource-manager")
    def post(self, request):
        """ Add permissions to a resource

        Add new permissions for a existing group and resource object

        Args:
            request: Django rest framework request

        Returns:
            Http status code

        """
        if 'permissions' not in request.data:
            return BossHTTPError("Permission are not included in the request", ErrorCodes.INVALID_URL)
        else:
            perm_list = dict(request.data)['permissions']

        if 'group' not in request.data:
            return BossHTTPError("Group are not included in the request", ErrorCodes.INVALID_URL)

        if 'collection' not in request.data:
            return BossHTTPError("Invalid resource or missing resource name in request", ErrorCodes.INVALID_URL)

        group_name = request.data.get('group', None)
        collection = request.data.get('collection', None)
        experiment = request.data.get('experiment', None)
        channel = request.data.get('channel', None)

        try:
            # Bosspublic can only have read permission
            if group_name == 'bosspublic' and not (set(perm_list).issubset({'read','read_volumetric_data'})):
                return BossHTTPError("The bosspublic group can only have read permissions",
                                     ErrorCodes.INVALID_POST_ARGUMENT)

            # If the user is not a member or maintainer of the group, they cannot assign permissions
            if not check_is_member_or_maintainer(request.user, group_name):
                return BossHTTPError('The user {} is not a member or maintainer of the group {} '.
                                     format(request.user.username, group_name), ErrorCodes.MISSING_PERMISSION)

            resource_object = self.get_object(collection, experiment, channel)
            if resource_object is None:
                return BossHTTPError("Unable to validate the resource", ErrorCodes.UNABLE_TO_VALIDATE)
            resource = resource_object[0]
            if request.user.has_perm("assign_group", resource):
                BossPermissionManager.add_permissions_group(group_name, resource, perm_list)
                return Response(status=status.HTTP_201_CREATED)
            else:
                return BossPermissionError('assign group', collection)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except Permission.DoesNotExist:
            return BossHTTPError("Invalid permissions in post".format(request.data['permissions']),
                                 ErrorCodes.UNRECOGNIZED_PERMISSION)
        except BossError as err:
            return err.to_http()

    @transaction.atomic
    @check_role("resource-manager")
    def patch(self, request):
        """ Patch permissions for a resource

        Remove specific permissions for a existing group and resource object
        Args:
            request: Django rest framework request
        Returns:
            Http status code

        """
        if 'permissions' not in request.data:
            return BossHTTPError("Permission are not included in the request", ErrorCodes. UNABLE_TO_VALIDATE)
        else:
            perm_list = dict(request.data)['permissions']

        if 'group' not in request.data:
            return BossHTTPError("Group are not included in the request", ErrorCodes. UNABLE_TO_VALIDATE)

        if 'collection' not in request.data:
            return BossHTTPError("Invalid resource or missing resource name in request", ErrorCodes. UNABLE_TO_VALIDATE)

        group_name = request.data.get('group', None)
        collection = request.data.get('collection', None)
        experiment = request.data.get('experiment', None)
        channel = request.data.get('channel', None)

        try:
            # Bosspublic can only have read permission
            if group_name == 'bosspublic' and (len(perm_list) != 1 or perm_list[0] != 'read'):
                return BossHTTPError("The bosspublic group can only have read permissions",
                                     ErrorCodes.INVALID_POST_ARGUMENT)
            # If the user is not a member or maintainer of the group, they cannot patch permissions
            if not check_is_member_or_maintainer(request.user, group_name):
                return BossHTTPError('The user {} is not a member or maintainer of the group {} '.
                                     format(request.user.username, group_name), ErrorCodes.MISSING_PERMISSION)

            resource_object = self.get_object(collection, experiment, channel)
            if resource_object is None:
                return BossHTTPError("Unable to validate the resource", ErrorCodes.UNABLE_TO_VALIDATE)

            resource = resource_object[0]
            # remove all existing permission for the group
            if request.user.has_perm("remove_group", resource) and request.user.has_perm("assign_group", resource):
                BossPermissionManager.delete_all_permissions_group(group_name, resource)
                BossPermissionManager.add_permissions_group(group_name, resource, perm_list)
                return Response(status=status.HTTP_200_OK)
            else:
                return BossPermissionError('remove group', resource.name)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except Permission.DoesNotExist:
            return BossHTTPError("Invalid permissions in post".format(request.data['permissions']),
                                 ErrorCodes.UNRECOGNIZED_PERMISSION)
        except BossError as err:
            return err.to_http()

    @transaction.atomic
    @check_role("resource-manager")
    def delete(self, request):
        """ Delete permissions for a resource object

       Remove specific permissions for a existing group and resource object

       Args:
            request: Django rest framework request
       Returns:
            Http status code

       """
        if 'group' not in request.query_params:
            return BossHTTPError("Group are not included in the request", ErrorCodes.INVALID_URL)

        if 'collection' not in request.query_params:
            return BossHTTPError("Invalid resource or missing resource name in request", ErrorCodes.INVALID_URL)

        group_name = request.query_params.get('group', None)
        collection = request.query_params.get('collection', None)
        experiment = request.query_params.get('experiment', None)
        channel = request.query_params.get('channel', None)
        try:
            if not check_is_member_or_maintainer(request.user, group_name):
                return BossHTTPError('The user {} is not a member or maintainer of the group {} '.
                                     format(request.user.username, group_name), ErrorCodes.MISSING_PERMISSION)

            resource_object = self.get_object(collection, experiment, channel)
            if resource_object is None:
                return BossHTTPError("Unable to validate the resource", ErrorCodes.UNABLE_TO_VALIDATE)

            if request.user.has_perm("remove_group", resource_object[0]):
                BossPermissionManager.delete_all_permissions_group(group_name, resource_object[0])
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return BossPermissionError('remove group', resource_object[0].name)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except Permission.DoesNotExist:
            return BossHTTPError("Invalid permissions in post".format(request.data['permissions']),
                                 ErrorCodes.UNRECOGNIZED_PERMISSION)
        except Exception as e:
            return BossHTTPError("{}".format(e), ErrorCodes.UNHANDLED_EXCEPTION)
        except BossError as err:
            return err.to_http()
