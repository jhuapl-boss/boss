from . import api

def get_perms(request, collection=None, experiment=None, channel=None, group=None):
    perms, err = api.get_perms(request, collection, experiment, channel, group)
    if err:
        return (None, err)

    def gen_key(ps):
        if group:
            key = ps['collection']
            if 'experiment' in ps:
                key += '/' + ps['experiment']
                if 'channel' in ps:
                    key += '/' + ps['channel']
        else:
            key = ps['group']
        return key

    # read, add, update, delete, assign_group, remove_group, 
    t = True; f = False;
    read    = [t,f,f,f,f,f]
    write   = [t,t,t,f,f,f]
    admin   = [t,t,t,f,t,t]
    admin_d = [t,t,t,t,t,t]

    # read_volumetric_data, add_volumetric_data , delete_volumetric_data 
    read_v = [t,f,f]
    add_v  = [t,t,f]
    del_v  = [t,t,t]

    def make_selection(p,is_chan):
        chk = [
            'read' in p,
            'add' in p,
            'update' in p,
            'delete' in p,
            'assign_group' in p,
            'remove_group' in p,
        ]

        chk_v = [
            'read_volumetric_data' in p,
            'add_volumetric_data' in p,
            'delete_volumetric_data' in p,
        ]

        perm = None
        if not is_chan:
            if chk == read:
                perm = "read"
            elif chk == write:
                perm = "write"
            elif chk == admin:
                perm = "admin"
            elif chk == admin_d:
                perm = "admin+delete"
            else:
                perm = "Raw: " + ", ".join(p)
        else:
            if chk == read and chk_v == read_v:
                perm = "read"
            elif chk == write and chk_v == add_v:
                perm = "write"
            elif chk == admin and chk_v == add_v: # make sure admin has proper permissions
                perm = "admin"
            elif chk == admin_d and chk_v == del_v:
                perm = "admin+delete"
            else:
                perm = "Raw: " + ", ".join(p)
        return perm

    perm_rows = {}
    for perm in perms:
        perm_rows[gen_key(perm)] = make_selection(perm['permissions'], perm.get('channel'))
    # Sort based on group name, so list is always in the same order
    perm_rows = list(perm_rows.items())
    perm_rows.sort(key = lambda x: x[0])
    return (perm_rows, None)

def set_perms(request, form, collection=None, experiment=None, channel=None, group=None):
    data = form.cleaned_data.copy()

    if 'collection' not in data and collection:
        data['collection'] = collection
        if 'experiment' not in data and experiment:
            data['experiment'] = experiment
            if 'channel' not in data and channel:
                data['channel'] = channel

    if 'group' not in data and group:
        data['group'] = group

    perms = data['permissions']
    if perms == "read":
        perms = ['read']
    elif perms == "write":
        perms = ['read', 'add', 'update']
    elif perms == "admin":
        perms = ['read', 'add', 'update', 'assign_group', 'remove_group']
    elif perms == "admin+delete":
        perms = ['read', 'add', 'update', 'delete', 'assign_group', 'remove_group']
    else:
        raise Exception("Unknown permissions: " + perms)

    if data.get('channel'):
        if 'read' in perms:
            perms.append('read_volumetric_data')
        if 'add' in perms:
            perms.append('add_volumetric_data')
        if 'delete' in perms:
            perms.append('delete_volumetric_data')

    data['permissions'] = perms

    collection = data.get('collection')
    experiment = data.get('experiment')
    channel = data.get('channel')
    group = data.get('group')
    perms, err = api.get_perms(request, collection, experiment, channel, group)
    if len(perms) > 0: # If perms for the group / resources already exists
        err = api.up_perms(request, data)
    else:
        err = api.add_perms(request, data)

    if err:
        return err
