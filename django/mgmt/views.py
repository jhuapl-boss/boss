from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from .forms import UserForm, RoleForm, GroupForm, GroupMemberForm
from .forms import CollectionForm, ExperimentForm, ChannelForm
from .forms import CoordinateFrameForm, MetaForm
from .forms import ResourcePermissionsForm, GroupPermissionsForm

from . import api
from . import utils

# import as to deconflict with our Token class
from rest_framework.authtoken.models import Token as TokenModel

# DP NOTE: If a form fails validation in the post() method, then
#          the populated form is passed to the get() method to
#          generate the same submission page, but with a form
#          that displays the validation errors

def redirect_frag(page, *args, frag=None):
    url = reverse(page, args=[*args])
    if frag:
        url += '#' + frag
    return redirect(url)

class Home(LoginRequiredMixin, View):
    def get(self, request):
        return HttpResponse(render_to_string('base.html', RequestContext(request)))

class Users(LoginRequiredMixin, View):
    def get(self, request, user_form=None):
        delete = request.GET.get('delete')
        if delete:
            err = api.del_user(request, delete)
            if err:
                return err
            return redirect('mgmt:users')

        users, err = api.get_users(request) # search query parameter will be automatically passed
        if err:
            return err

        headers = ["Username", "Actions"]
        fmt_usr = '<a href="{}">{}</a>'
        fmt_act = '<a href="?delete={}">Remove User</a>'
        fmt = lambda u: (fmt_usr.format(reverse('mgmt:user',args=[u['username']]), u['username']), fmt_act.format(u['username']))
        users_args = utils.make_pagination(request, headers, users, fmt)

        args = {
            'users': users_args,
            'user_form': user_form if user_form else UserForm(),
            'user_error': "error" if user_form else "",
        }
        return HttpResponse(render_to_string('users.html', args, RequestContext(request)))

    def post(self, request):
        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            username = data['username']
            del data['username']
            del data['verify_password']

            err = api.add_user(request, username, data)
            if err:
                form.add_error(None, err)
            else:
                return redirect('mgmt:users')
        return self.get(request, user_form=form)

class User(LoginRequiredMixin, View):
    def get(self, request, username, role_form=None):
        remove = request.GET.get('remove')
        if remove is not None:
            err = api.del_role(request, username, remove)
            if err:
                return err
            return redirect_frag('mgmt:user', username, frag='Roles')

        user, err = api.get_user(request, username)
        if err:
            return err

        rows = []
        rows.append(('Username', user['username']))
        rows.append(('First Name', user.get('firstName', '')))
        rows.append(('Last Name', user.get('lastName', '')))
        rows.append(('Email', user.get('email', '')))

        roles = user['realmRoles']
        headers = ["Roles", "Actions"]
        fmt = lambda r: (r, '<a href="?remove={}#Role">Remove Role</a>'.format(r))
        roles_args = utils.make_pagination(request, headers, roles, fmt, frag='#Roles')

        args = {
            'username': username,
            'rows': rows,
            'roles': roles_args,
            'role_form': role_form if role_form else RoleForm(),
            'role_error': "error" if role_form else "",
        }
        return HttpResponse(render_to_string('user.html', args, RequestContext(request)))

    def post(self, request, username):
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']

            err = api.add_role(request, username, role)
            if err:
                form.add_error(None, err)
            else:
                return redirect_frag('mgmt:user', username, frag='Roles')
        return self.get(request, username, role_form=form)

class Token(LoginRequiredMixin, View):
    def get(self, request):
        try:
            token = TokenModel.objects.get(user = request.user)
            button = "Revoke Token"
        except:
            token = None
            button = "Generate Token"

        args = {
            'username': request.user,
            'token': token,
            'button': button,
        }
        return HttpResponse(render_to_string('token.html', args, RequestContext(request)))

    def post(self, request):
        try:
            token = TokenModel.objects.get(user = request.user)
            token.delete()
        except:
            token = TokenModel.objects.create(user = request.user)

        return redirect('mgmt:token')

class Groups(LoginRequiredMixin, View):
    def get(self, request, group_form=None):
        delete = request.GET.get('delete')
        if delete:
            err = api.del_group(request, delete)
            if err:
                return err
            return redirect('mgmt:groups')

        # can only modify groups the user is a maintainer of
        groups, err = api.get_groups(request, maintainer_only=True)
        if err:
            return err

        headers = ["Group", "Actions"]
        fmt_grp = '<a href="{}">{}</a>'
        fmt_act = '<a href="?delete={}">Remove Group</a>'
        fmt = lambda g: (fmt_grp.format(reverse('mgmt:group',args=[g]), g), fmt_act.format(g))
        groups_args = utils.make_pagination(request, headers, groups, fmt)

        args = {
            'groups': groups_args,
            'group_form': group_form if group_form else GroupForm(),
            'group_error': "error" if group_form else ""
        }
        return HttpResponse(render_to_string('groups.html', args, RequestContext(request)))

    def post(self, request):
        form = GroupForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']

            err = api.add_group(request, group_name)
            if err:
                form.add_error(None, err)
            else:
                return redirect('mgmt:groups')
        return self.get(request, group_form=form)

class Group(LoginRequiredMixin, View):
    def get(self, request, group_name, memb_form=None, perms_form=None):
        remove = request.GET.get('rem_memb')
        if remove is not None:
            err = api.del_member(request, group_name, remove)
            if err:
                return err
            return redirect('mgmt:group', group_name)

        remove = request.GET.get('rem_maint')
        if remove is not None:
            err = api.del_maintainer(request, group_name, remove)
            if err:
                return err
            return redirect('mgmt:group', group_name)

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, *remove.split('/'), group=group_name)
            if err:
                return err
            return redirect_frag('mgmt:group', group_name, frag='Permissions')

        members, err = api.get_members(request, group_name)
        if err:
            return err

        maintainers, err = api.get_maintainers(request, group_name)
        if err:
            return err

        perms, err = utils.get_perms(request, group=group_name)
        if err:
            return err

        users = list(members)
        for user in maintainers:
            if user not in users:
                users.append(user)

        def fmt(m):
            perms = []
            actions = []
            if m in members:
                perms.append('member')
                actions.append('<a href="?rem_memb={}">Remove Member</a>'.format(m))
            if m in maintainers:
                perms.append('maintainer')
                actions.append('<a href="?rem_maint={}">Remove Mmaintainer</a>'.format(m))
            perms = '+'.join(perms)
            actions = '<br/>'.join(actions)
            return (m, perms, actions)

        headers = ["User", "Permissions", "Actions"]
        users_args = utils.make_pagination(request, headers, users, fmt)

        perms_args = utils.make_perms_pagination(request, perms, 'Resources')

        args = {
            'group_name': group_name,
            'users': users_args,
            'members': members,
            'maintainers': maintainers,
            'perms': perms_args,
            'memb_form': memb_form if memb_form else GroupMemberForm(),
            'memb_error': "error" if memb_form else "",
            'perms_form': perms_form if perms_form else GroupPermissionsForm(),
            'perms_error': "error" if perms_form else "",
        }
        return HttpResponse(render_to_string('group.html', args, RequestContext(request)))

    def post(self, request, group_name):
        action = request.GET.get('action') # URL parameter

        if action == 'memb':
            form = GroupMemberForm(request.POST)
            if form.is_valid():
                user = form.cleaned_data['user']
                role = form.cleaned_data['role']

                if 'member' in role:
                    memb_err = api.add_member(request, group_name, user)
                    if memb_err:
                        form.add_error(None, memb_err)

                if 'maintainer' in role:
                    maint_err = api.add_maintainer(request, group_name, user)
                    if maint_err:
                        form.add_error(None, maint_err)

                if not memb_error and not maint_err:
                    return redirect('mgmt:group', group_name)
            return self.get(request, group_name, memb_form=form)
        elif action == 'perms':
            form = GroupPermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, group=group_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:group', group_name, frag='Permissions')
            return self.get(request, group_name, perms_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")

class Resources(LoginRequiredMixin, View):
    def get(self, request, col_form=None, coord_form=None):
        delete = request.GET.get('del_col')
        if delete:
            err = api.del_collection(request, delete)
            if err:
                return err
            return redirect('mgmt:resources')

        delete = request.GET.get('del_coord')
        if delete:
            err = api.del_coord(request, delete)
            if err:
                return err
            return redirect_frag('mgmt:resources', frag='CoordinateFrames')

        collections, err = api.get_collections(request)
        if err:
            return err

        coords, err = api.get_coords(request)
        if err:
            return err

        headers = ["Collection", "Actions"]
        fmt_lnk = '<a href="{}">{}</a>'
        fmt_act = '<a href="?del_col={}">Remove Collection</a>'
        fmt = lambda r: (fmt_lnk.format(reverse('mgmt:collection',args=[r]), r), fmt_act.format(r))
        collections_args = utils.make_pagination(request, headers, collections, fmt)

        headers = ["Coordinate Frame", "Actions"]
        fmt_lnk = '<a href="{}">{}</a>'
        fmt_act = '<a href="?del_coord={}">Remove Coordinate Frame</a>'
        fmt = lambda r: (fmt_lnk.format(reverse('mgmt:coord',args=[r]), r), fmt_act.format(r))
        coords_args = utils.make_pagination(request, headers, coords, fmt)

        args = {
            'collections': collections_args,
            'coords': coords_args,
            'col_form': col_form if col_form else CollectionForm(),
            'col_error': "error" if col_form else "",
            'coord_form': coord_form if coord_form else CoordinateFrameForm(),
            'coord_error': "error" if coord_form else "",
        }
        return HttpResponse(render_to_string('collections.html', args, RequestContext(request)))

    def post(self, request):
        action = request.GET.get('action') # URL parameter

        if action == 'col':
            form = CollectionForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                collection = data['name']

                err = api.add_collection(request, collection, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:resources')
            return self.get(request, col_form=form)
        elif action == 'coord':
            form = CoordinateFrameForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                coord_name = data['name']

                err = api.add_coord(request, coord_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:resources', frag='CoordinateFrames')
            return self.get(request, coord_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")

class CoordinateFrame(LoginRequiredMixin, View):
    def get(self, request, coord_name, coord_form=None):
        if not coord_form:
            coord, err = api.get_coord(request, coord_name)
            if err:
                return err
            coord_form = CoordinateFrameForm(coord).is_update()
            coord_error = ""
        else:
            coord_form.is_update()
            coord_error = "error"

        args = {
            'coord_name': coord_name,
            'coord_form': coord_form,
            'coord_error': coord_error,
        }
        return HttpResponse(render_to_string('coordinate_frame.html', args, RequestContext(request)))

    def post(self, request, coord_name):
            form = CoordinateFrameForm(request.POST)
            if form.is_valid():
                data = form.cleaned_update_data

                err = api.up_coord(request, coord_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:coord', data['name'])
            return self.get(request, coord_name, coord_form=form)

class Collection(LoginRequiredMixin, View):
    def get(self, request, collection_name, col_form=None, exp_form=None, meta_form=None, perms_form=None):
        remove = request.GET.get('rem_exp')
        if remove is not None:
            err = api.del_experiment(request, collection_name, remove)
            if err:
                return err
            return redirect_frag('mgmt:collection', collection_name, frag='Experiments')

        remove = request.GET.get('rem_meta')
        if remove is not None:
            err = api.del_meta(request, remove, collection_name)
            if err:
                return err
            return redirect_frag('mgmt:collection', collection_name, frag='Meta')

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, collection_name, group=remove)
            if err:
                return err
            return redirect_frag('mgmt:collection', collection_name, frag='Permissions')

        collection, err = api.get_collection(request, collection_name)
        if err:
            return err

        if not col_form:
            col_form = CollectionForm(collection)
            col_error = ""
        else:
            col_error = "error"

        metas, err = api.get_meta_keys(request, collection_name)
        if err:
            return err

        perms, err = utils.get_perms(request, collection_name)
        if err:
            return err

        headers = ["Experiment", "Actions"]
        fmt_lnk = '<a href="{}">{}</a>'
        fmt_act = '<a href="?rem_exp={}">Remove Experiment</a>'
        fmt = lambda r: (fmt_lnk.format(reverse('mgmt:experiment',args=[collection_name, r]), r), fmt_act.format(r))
        experiments_args = utils.make_pagination(request, headers, collection['experiments'], fmt)

        meta_url = reverse('mgmt:meta', args=[collection_name])
        metas_args = utils.make_metas_pagination(request, metas, 'Collection', meta_url)
        perms_args = utils.make_perms_pagination(request, perms)

        args = {
            'collection_name': collection_name,
            'collection': collection,
            'experiments': experiments_args,
            'metas': metas_args,
            'perms': perms_args,
            'col_form': col_form,
            'col_error': col_error,
            'exp_form': exp_form if exp_form else ExperimentForm(),
            'exp_error': "error" if exp_form else "",
            'meta_form': meta_form if meta_form else MetaForm(),
            'meta_error': "error" if meta_form else "",
            'perms_form': perms_form if perms_form else ResourcePermissionsForm(),
            'perms_error': "error" if perms_form else "",
        }
        return HttpResponse(render_to_string('collection.html', args, RequestContext(request)))

    def post(self, request, collection_name):
        action = request.GET.get('action') # URL parameter

        if action == 'exp':
            form = ExperimentForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                experiment_name = data['name']

                err = api.add_experiment(request, collection_name, experiment_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:collection', collection_name, frag='Experiments')
            return self.get(request, collection_name, exp_form=form)
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:collection', collection_name, frag='Meta')
            return self.get(request, collection_name, meta_form=form)
        elif action == 'perms':
            form = ResourcePermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, collection_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:collection', collection_name, frag='Permissions')
            return self.get(request, collection_name, perms_form=form)
        elif action == 'update':
            form = CollectionForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()

                err = api.up_collection(request, collection_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:collection', data['name'])
            return self.get(request, collection_name, col_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")

class Experiment(LoginRequiredMixin, View):
    def get(self, request, collection_name, experiment_name, exp_form=None, chan_form=None, meta_form=None, perms_form=None):
        remove = request.GET.get('rem_chan')
        if remove is not None:
            err = api.del_channel(request, collection_name, experiment_name, remove)
            if err:
                return err
            return redirect_frag('mgmt:experiment', collection_name, experiment_name, frag='Channels')

        remove = request.GET.get('rem_meta')
        if remove is not None:
            err = api.del_meta(request, remove, collection_name, experiment_name)
            if err:
                return err
            return redirect_frag('mgmt:experiment', collection_name, experiment_name, frag='Meta')

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, collection_name, experiment, group=remove)
            if err:
                return err
            return redirect_frag('mgmt:experiment', collection_name, experiment_name, frag='Permissions')

        experiment, err = api.get_experiment(request, collection_name, experiment_name)
        if err:
            return err

        if not exp_form:
            exp_form = ExperimentForm(experiment).is_update()
            exp_error = ""
        else:
            exp_form.is_update()
            exp_error = "error"

        channels, err = api.get_channels(request, collection_name, experiment_name)
        if err:
            return err

        metas, err = api.get_meta_keys(request, collection_name, experiment_name)
        if err:
            return err

        perms, err = utils.get_perms(request, collection_name, experiment_name)
        if err:
            return err

        headers = ["Channel", "Actions"]
        fmt_lnk = '<a href="{}">{}</a>'
        fmt_act = '<a href="?rem_chan={}">Remove Channel</a>'
        fmt = lambda r: (fmt_lnk.format(reverse('mgmt:channel',args=[collection_name, experiment_name, r]), r), fmt_act.format(r))
        channels_args = utils.make_pagination(request, headers, channels, fmt)

        meta_url = reverse('mgmt:meta', args=[collection_name, experiment_name])
        metas_args = utils.make_metas_pagination(request, metas, 'Experiment', meta_url)
        perms_args = utils.make_perms_pagination(request, perms)

        args = {
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'experiment': experiment,
            'channels': channels_args,
            'metas': metas_args,
            'perms': perms_args,
            'exp_form': exp_form,
            'exp_error': exp_error,
            'chan_form': chan_form if chan_form else ChannelForm(),
            'chan_error': "error" if chan_form else "",
            'meta_form': meta_form if meta_form else MetaForm(),
            'meta_error': "error" if meta_form else "",
            'perms_form': perms_form if perms_form else ResourcePermissionsForm(),
            'perms_error': "error" if perms_form else "",
        }
        return HttpResponse(render_to_string('experiment.html', args, RequestContext(request)))

    def post(self, request, collection_name, experiment_name):
        action = request.GET.get('action') # URL parameter

        if action == 'chan':
            form = ChannelForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                channel_name = data['name']

                err = api.add_channel(request, collection_name, experiment_name, channel_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:experiment', collection_name, experiment_name, frag='Channels')
            return self.get(request, collection_name, experiment_name, exp_form=form)
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name, experiment_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:experiment', collection_name, experiment_name, frag='Meta')
            return self.get(request, collection_name, experiment_name, meta_form=form)
        elif action == 'perms':
            form = ResourcePermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, collection_name, experiment_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:experiment', collection_name, experiment_name, frag='Permissions')
            return self.get(request, collection_name, experiment_name, perms_form=form)
        elif action == 'update':
            form = ExperimentForm(request.POST)
            if form.is_valid():
                data = form.cleaned_update_data

                err = api.up_experiment(request, collection_name, experiment_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:experiment', collection_name, data['name'])
            return self.get(request, collection_name, experiment_name, exp_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")

class Channel(LoginRequiredMixin, View):
    def get(self, request, collection_name, experiment_name, channel_name, chan_form=None, meta_form=None, perms_form=None):
        remove = request.GET.get('rem_meta')
        if remove is not None:
            err = api.del_meta(request, remove, collection_name, experiment_name, channel_name)
            if err:
                return err
            return redirect_frag('mgmt:channel', collection_name, experiment_name, channel_name, frag='Meta')

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, collection_name, experiment, channel, group=remove)
            if err:
                return err
            return redirect_frag('mgmt:channel', collection_name, experiment_name, channel_name, frag='Permissions')

        channel, err = api.get_channel(request, collection_name, experiment_name, channel_name)
        if err:
            return err

        if not chan_form:
            chan_form = ChannelForm(channel).is_update()
            chan_error = ""
        else:
            chan_form.is_update()
            chan_error = "error"

        metas, err = api.get_meta_keys(request, collection_name, experiment_name, channel_name)
        if err:
            return err

        perms, err = utils.get_perms(request, collection_name, experiment_name, channel_name)
        if err:
            return err

        meta_url = reverse('mgmt:meta', args=[collection_name, experiment_name, channel_name])
        metas_args = utils.make_metas_pagination(request, metas, 'Channel', meta_url)
        perms_args = utils.make_perms_pagination(request, perms)

        args = {
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'channel_name': channel_name,
            'channel': channel,
            'metas': metas_args,
            'perms': perms_args,
            'chan_form': chan_form,
            'chan_error': chan_error,
            'meta_form': meta_form if meta_form else MetaForm(),
            'meta_error': "error" if meta_form else "",
            'perms_form': perms_form if perms_form else ResourcePermissionsForm(),
            'perms_error': "error" if perms_form else "",
        }
        return HttpResponse(render_to_string('channel.html', args, RequestContext(request)))

    def post(self, request, collection_name, experiment_name, channel_name):
        action = request.GET.get('action') # URL parameter

        if action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name, experiment_name, channel_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:channel', collection_name, experiment_name, channel_name, frag='Meta')
            return self.get(request, collection_name, experiment_name, channel_name, meta_form=form)
        elif action == 'perms':
            form = ResourcePermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, collection_name, experiment_name, channel_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect_frag('mgmt:channel', collection_name, experiment_name, channel_name, frag='Permissions')
            return self.get(request, collection_name, experiment_name, channel_name, perms_form=form)
        elif action == 'update':
            form = ChannelForm(request.POST)
            if form.is_valid():
                data = form.cleaned_update_data

                err = api.up_channel(request, collection_name, experiment_name, channel_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:channel', collection_name, experiment_name, data['name'])
            return self.get(request, collection_name, experiment_name, channel_name, chan_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")

class Meta(LoginRequiredMixin, View):
    def get(self, request, collection, experiment=None, channel=None, meta_form=None):
        if not meta_form:
            key = request.GET['key']
            meta, err = api.get_meta(request, key, collection, experiment, channel)
            if err:
                return err
            meta_form = MetaForm(meta).is_update()
            meta_error = ""
        else:
            meta_form.is_update()
            meta_error = "error"

        if channel is not None:
            category = "Channel"
            category_name = channel
        elif experiment is not None:
            category = "Experiment"
            category_name = experiment
        else:
            category = "Collection"
            category_name = collection

        args = {
            'category': category,
            'category_name': category_name,
            'meta_form': meta_form,
            'meta_error': meta_error,
        }
        return HttpResponse(render_to_string('meta.html', args, RequestContext(request)))

    def post(self, request, collection, experiment=None, channel=None):
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.up_meta(request, key, value, collection, experiment, channel)
                if err:
                    form.add_error(None, err)
                else:
                    return HttpResponseRedirect('?key=' + key)
            return self.get(request, collection, experiment, channel, meta_form=form)

