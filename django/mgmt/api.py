from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template import RequestContext
from django.conf import settings

from sso.views.views_user import BossUser, BossUserRole
from bosscore.views.views_group import BossUserGroup, BossGroupMaintainer, BossGroupMember
from bosscore.views.views_resource import CollectionList, CollectionDetail
from bosscore.views.views_resource import ExperimentList, ExperimentDetail
from bosscore.views.views_resource import CoordinateFrameList, CoordinateFrameDetail
from bosscore.views.views_resource import ChannelList, ChannelDetail
from bosscore.views.views_permission import ResourceUserPermission
from bossmeta.views import BossMeta

from rest_framework import status

import json

def error_message(resp):
    try:
        data = json.loads(resp.content.decode('ASCII'))
        if 'message' in data:
            return data['message']
        elif 'detail' in data:
            return data['detail']
        else:
            return str(resp.content)
            return "" # DP TODO: create an appropriate generic error message
    except:
        return str(resp.content)

def error_response(request, resp, category, category_name=None):
    args = {
        'category': category,
        'category_name': category_name,
        'message': error_message(resp),
    }

    page = render_to_string('error.html', args, RequestContext(request))
    return HttpResponse(page, status=resp.status_code)


def _get(category, cls, request, *args):
    boss = cls()
    boss.request = request # needed for check_role() to work
    resp = boss.get(request, *args)
    if not status.is_success(resp.status_code):
        category_name = args[-1] if len(args) > 0 else None
        return (None, error_response(request, resp, category, category_name))
    return (resp.data, None)

def _del(category, cls, request, *args):
    boss = cls()
    boss.request = request # needed for check_role() to work
    resp = boss.delete(request, *args)
    if not status.is_success(resp.status_code):
        category_name = args[-1] if len(args) > 0 else None
        return error_response(request, resp, category, category_name)
    return None

def _post(category, cls, request, data, *args):
    boss = cls()
    boss.request = request # needed for check_role() to work
    if data:
        boss.request.data = data # simulate the DRF request object
    resp = boss.post(request, *args)
    if not status.is_success(resp.status_code):
        return error_message(resp)
    return None

def _put(category, cls, request, data, *args):
    boss = cls()
    boss.request = request # needed for check_role() to work
    if data:
        boss.request.data = data # simulate the DRF request object
    resp = boss.put(request, *args)
    if not status.is_success(resp.status_code):
        return error_message(resp)
    return None

def _patch(category, cls, request, data, *args):
    boss = cls()
    boss.request = request # needed for check_role() to work
    if data:
        boss.request.data = data # simulate the DRF request object
    resp = boss.patch(request, *args)
    if not status.is_success(resp.status_code):
        return error_message(resp)
    return None

"""SSO API for Users and Roles"""
def get_users(request):
    return _get('Users', BossUser, request)

def get_user(request, username):
    return _get('User', BossUser, request, username)

def del_user(request, username):
    return _del('User', BossUser, request, username)

def add_user(request, username, data):
    return _post('User', BossUser, request, data, username)

def get_roles(request, username):
    return _get('User', BossUserRole, request, username)

def del_role(request, username, role):
    return _del('Role', BossUserRole, request, username, role)

def add_role(request, username, role):
    return _post('Role', BossUserRole, request, None, username, role)


"""BOSS API for Groups and Group Members / Maintainers"""
def get_groups(request, maintainer_only=True):
    if maintainer_only:
        request.query_params = {}
        request.query_params['filter'] = 'maintainer'
    data, err = _get('Groups', BossUserGroup, request)
    if data:
        data = data['groups']
    return (data, err)

def del_group(request, group):
    return _del('Group', BossUserGroup, request, group)

def add_group(request, group):
    return _post('Group', BossUserGroup, request, None, group)

def get_members(request, group):
    data, err = _get('Group Members', BossGroupMember, request, group)
    if data:
        data = data['members']
    return (data, err)

def del_member(request, group, member):
    return _del('Group Member', BossGroupMember, request, group, member)

def add_member(request, group, member):
    return _post('Group Member', BossGroupMember, request, None, group, member)

def get_maintainers(request, group):
    data, err = _get('Group Maintainers', BossGroupMaintainer, request, group)
    if data:
        data = data['maintainers']
    return (data, err)

def del_maintainer(request, group, maintainer):
    return _del('Group Maintainer', BossGroupMaintainer, request, group, maintainer)

def add_maintainer(request, group, maintainer):
    return _post('Group Maintainer', BossGroupMaintainer, request, None, group, maintainer)

"""BOSS API for Coordinate Frames, Collections, Experiments, and Channels"""
# Coordinate Frames
def get_coords(request):
    data, err = _get('Coordinate Frames', CoordinateFrameList, request)
    if data:
        data = data['coords']
    return (data, err)

def get_coord(request, coord):
    return _get('Coordinate Frame', CoordinateFrameDetail, request, coord)

def del_coord(request, coord):
    return _del('Coordinate Frame', CoordinateFrameDetail, request, coord)

def add_coord(request, coord, data):
    return _post('Coordinate Frame', CoordinateFrameDetail, request, data, coord)

def up_coord(request, coord, data):
    return _put('Coordinate Frame', CoordinateFrameDetail, request, data, coord)

# Collections
def get_collections(request):
    data, err = _get('Collections', CollectionList, request)
    if data:
        data = data['collections']
    return (data, err)

def get_collection(request, collection):
    return _get('Collection', CollectionDetail, request, collection)

def del_collection(request, collection):
    return _del('Collection', CollectionDetail, request, collection)

def add_collection(request, collection, data):
    return _post('Collection', CollectionDetail, request, data, collection)

def up_collection(request, collection, data):
    return _put('Collection', CollectionDetail, request, data, collection)

# Experiments
def get_experiments(request, collection):
    data, err = _get('Experiments', ExperimentList, request, collection)
    if data:
        data = data['experiments']
    return (data, err)

def get_experiment(request, collection, experiment):
    return _get('Experiment', ExperimentDetail, request, collection, experiment)

def del_experiment(request, collection, experiment):
    return _del('Experiment', ExperimentDetail, request, collection, experiment)

def add_experiment(request, collection, experiment, data):
    return _post('Experiment', ExperimentDetail, request, data, collection, experiment)

def up_experiment(request, collection, experiment, data):
    return _put('Experiment', ExperimentDetail, request, data, collection, experiment)

# Channels
def get_channels(request, collection, experiment):
    data, err = _get('Channels', ChannelList, request, collection, experiment)
    if data:
        data = data['channels']
    return (data, err)

def get_channel(request, collection, experiment, channel):
    return _get('Channel', ChannelDetail, request, collection, experiment, channel)

def del_channel(request, collection, experiment, channel):
    return _del('Channel', ChannelDetail, request, collection, experiment, channel)

def add_channel(request, collection, experiment, channel, data):
    return _post('Channel', ChannelDetail, request, data, collection, experiment, channel)

def up_channel(request, collection, experiment, channel, data):
    return _put('Channel', ChannelDetail, request, data, collection, experiment, channel)

"""BOSS API for Metadata"""
def get_meta_keys(request, collection, experiment=None, channel=None):
    request.version = settings.BOSS_VERSION
    request.query_params = {}
    data, err = _get('Metadata', BossMeta, request, collection, experiment, channel)
    if data:
        data = data['keys']
    return (data, err)

def get_meta(request, key, collection, experiment=None, channel=None):
    request.version = settings.BOSS_VERSION
    request.query_params = {'key': key}
    return _get('Metadata', BossMeta, request, collection, experiment, channel)

def del_meta(request, key, collection, experiment=None, channel=None):
    request.version = settings.BOSS_VERSION
    request.query_params = {'key': key}
    return _del('Metadata', BossMeta, request, collection, experiment, channel)

def add_meta(request, key, value, collection, experiment=None, channel=None):
    request.version = settings.BOSS_VERSION
    request.query_params = {'key': key, 'value': value}
    return _post('Metadata', BossMeta, request, None, collection, experiment, channel)

def up_meta(request, key, value, collection, experiment=None, channel=None):
    request.version = settings.BOSS_VERSION
    request.query_params = {'key': key, 'value': value}
    return _put('Metadata', BossMeta, request, None, collection, experiment, channel)

"""BOSS API for Permissions"""
def get_perms(request, collection=None, experiment=None, channel=None, group=None):
    request.query_params = {}
    if collection:
        request.query_params['collection'] = collection
        if experiment:
            request.query_params['experiment'] = experiment
            if channel:
                request.query_params['channel'] = channel
    if group:
        request.query_params['group'] = group
    data, err = _get('Permissions', ResourceUserPermission, request)
    if data:
        data = data['permission-sets']
    return (data, err)

def del_perms(request, collection=None, experiment=None, channel=None, group=None):
    request.query_params = {}
    if collection:
        request.query_params['collection'] = collection
        if experiment:
            request.query_params['experiment'] = experiment
            if channel:
                request.query_params['channel'] = channel
    if group:
        request.query_params['group'] = group
    return _del('Permissions', ResourceUserPermission, request)

def add_perms(request, data):
    return _post('Permissions', ResourceUserPermission, request, data)

def up_perms(request, data):
    return _patch('Permissions', ResourceUserPermission, request, data)

