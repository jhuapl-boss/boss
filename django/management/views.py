from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

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

class Home(LoginRequiredMixin, View):
    def get(self, request):
        return HttpResponse(render_to_string('base.html'))

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

        args = {
            'users': users,
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
                return err
            return redirect('mgmt:users')
        else:
            return self.get(request, user_form=form)

class User(LoginRequiredMixin, View):
    def get(self, request, username, role_form=None):
        remove = request.GET.get('remove')
        if remove is not None:
            err = api.del_role(request, username, remove)
            if err:
                return err
            return redirect('mgmt:user', username)

        user, err = api.get_user(request, username)
        if err:
            return err

        rows = []
        rows.append(('Username', user['username']))
        rows.append(('First Name', user.get('firstName', '')))
        rows.append(('Last Name', user.get('lastName', '')))
        rows.append(('Email', user.get('email', '')))

        args = {
            'username': username,
            'rows': rows,
            'roles': user['realmRoles'],
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
                return err
            return redirect('mgmt:user', username)
        else:
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

        args = {
            'groups': groups,
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
                return err
            return redirect('mgmt:groups')
        else:
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
            return redirect('mgmt:group', group_name)

        members, err = api.get_members(request, group_name)
        if err:
            return err

        maintainers, err = api.get_maintainers(request, group_name)
        if err:
            return err

        data = {}
        for member in members:
            data[member] = 'member'
            if member in maintainers:
                data[member] += '+maintainer'
        for maintainer in maintainers:
            if maintainer not in members:
                data[maintainer] = 'maintainer'

        perms, err = utils.get_perms(request, group=group_name)
        if err:
            return err

        args = {
            'group_name': group_name,
            'rows': data.items(),
            'members': members,
            'maintainers': maintainers,
            'perms': perms,
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
                    err = api.add_member(request, group_name, user)
                    if err:
                        return err

                if 'maintainer' in role:
                    err = api.add_maintainer(request, group_name, user)
                    if err:
                        return err

                return redirect('mgmt:group', group_name)
            else:
                return self.get(request, group_name, memb_form=form)
        elif action == 'perms':
            form = GroupPermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, group=group_name)
                if err:
                    return err
                return redirect('mgmt:group', group_name)
            else:
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
            return redirect('mgmt:resources')

        collections, err = api.get_collections(request)
        if err:
            return err

        coords, err = api.get_coords(request)
        if err:
            return err

        args = {
            'collections': collections,
            'coords': coords,
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
                    return err
                return redirect('mgmt:resources')
            else:
                return self.get(request, col_form=form)
        elif action == 'coord':
            form = CoordinateFrameForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                coord_name = data['name']

                err = api.add_coord(request, coord_name, data)
                if err:
                    return err
                return redirect('mgmt:resources')
            else:
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
                    return err
                return redirect('mgmt:coord', data['name'])
            else:
                return self.get(request, coord_name, coord_form=form)

class Collection(LoginRequiredMixin, View):
    def get(self, request, collection_name, col_form=None, exp_form=None, meta_form=None, perms_form=None):
        remove = request.GET.get('rem_exp')
        if remove is not None:
            err = api.del_experiment(request, collection_name, remove)
            if err:
                return err
            return redirect('mgmt:collection', collection_name)

        remove = request.GET.get('rem_meta')
        if remove is not None:
            err = api.del_meta(request, remove, collection_name)
            if err:
                return err
            return redirect('mgmt:collection', collection_name)

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, collection_name, group=remove)
            if err:
                return err
            return redirect('mgmt:collection', collection_name)

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

        args = {
            'collection_name': collection_name,
            'collection': collection,
            'metas': metas,
            'perms': perms,
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
                    return err
                return redirect('mgmt:collection', collection_name)
            else:
                return self.get(request, collection_name, exp_form=form)
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name)
                if err:
                    return err
                return redirect('mgmt:collection', collection_name)
            else:
                return self.get(request, collection_name, meta_form=form)
        elif action == 'perms':
            form = ResourcePermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, collection_name)
                if err:
                    return err
                return redirect('mgmt:collection', collection_name)
            else:
                return self.get(request, collection_name, perms_form=form)
        elif action == 'update':
            form = CollectionForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()

                err = api.up_collection(request, collection_name, data)
                if err:
                    return err
                return redirect('mgmt:collection', data['name'])
            else:
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
            return redirect('mgmt:experiment', collection_name, experiment_name)

        remove = request.GET.get('rem_meta')
        if remove is not None:
            err = api.del_meta(request, remove, collection_name, experiment_name)
            if err:
                return err
            return redirect('mgmt:experiment', collection_name, experiment_name)

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, collection_name, experiment, group=remove)
            if err:
                return err
            return redirect('mgmt:experiment', collection_name, experiment_name)

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

        args = {
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'experiment': experiment,
            'channels': channels,
            'metas': metas,
            'perms': perms,
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
                    return err
                return redirect('mgmt:experiment', collection_name, experiment_name)
            else:
                return self.get(request, collection_name, experiment_name, exp_form=form)
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name, experiment_name)
                if err:
                    return err
                return redirect('mgmt:experiment', collection_name, experiment_name)
            else:
                return self.get(request, collection_name, experiment_name, meta_form=form)
        elif action == 'perms':
            form = ResourcePermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, collection_name, experiment_name)
                if err:
                    return err
                return redirect('mgmt:experiment', collection_name, experiment_name)
            else:
                return self.get(request, collection_name, experiment_name, perms_form=form)
        elif action == 'update':
            form = ExperimentForm(request.POST)
            if form.is_valid():
                data = form.cleaned_update_data

                err = api.up_experiment(request, collection_name, experiment_name, data)
                if err:
                    return err
                return redirect('mgmt:experiment', collection_name, data['name'])
            else:
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
            return redirect('mgmt:channel', collection_name, experiment_name, channel_name)

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, collection_name, experiment, channel, group=remove)
            if err:
                return err
            return redirect('mgmt:channel', collection_name, experiment_name, channel_name)

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

        args = {
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'channel_name': channel_name,
            'channel': channel,
            'metas': metas,
            'perms': perms,
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
                    return err
                return redirect('mgmt:channel', collection_name, experiment_name, channel_name)
            else:
                return self.get(request, collection_name, experiment_name, channel_name, meta_form=form)
        elif action == 'perms':
            form = ResourcePermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, collection_name, experiment_name, channel_name)
                if err:
                    return err
                return redirect('mgmt:channel', collection_name, experiment_name, channel_name)
            else:
                return self.get(request, collection_name, experiment_name, channel_name, perms_form=form)
        elif action == 'update':
            form = ChannelForm(request.POST)
            if form.is_valid():
                data = form.cleaned_update_data

                err = api.up_channel(request, collection_name, experiment_name, channel_name, data)
                if err:
                    return err
                return redirect('mgmt:channel', collection_name, experiment_name, data['name'])
            else:
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
                    return err
                return HttpResponseRedirect('?key=' + key)
            else:
                return self.get(request, collection, experiment, channel, meta_form=form)
