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

    # convert to format frontend wants
    perm_arr = []
    for r in perm_rows:
        perm_arr.append({"group": r[0], "permissions": r[1]})

    return (perm_arr, None)

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
    try:
        if len(perms) > 0: # If perms for the group / resources already exists
            err = api.up_perms(request, data)
        else:
            err = api.add_perms(request, data)
    except Exception as e:
        err = "Invalid group name."

    if err:
        return err

def make_pagination(request, headers, rows, row_fmt=None, param='page', page_size=10, window_size=5, frag=''):
    """Handle all of the logic needed to feed data to the mgmt paginated_table tag

    Args:
        request (Request) : Django request object
        headers (list) : List of table headers
        rows (list) : List of table row data that will be paginated
        row_fmt (func|None) : Transform function for each row in rows that will be displayed
                              Should transform the row to contain headers number of columns
        param (String) : the GET parameter to use to paginate the table
        page_size (int) : Number of elements to display on each page
        window_size (int) : Number of pagination links to display on the pagination bar
                            This should be an odd number to make sure the current page is center
        frag (String) : URL fragment to attach to each pagination URL
    """
    if row_fmt is None:
        row_fmt = lambda x: x

    current_page = int(request.GET.get(param, 1)) - 1 # zero index the page
    # Div Ceiling - from http://stackoverflow.com/a/17511341
    total_pages = -(-len(rows) // page_size)
    if total_pages == 0:
        total_pages = 1
    if current_page >= total_pages:
        raise Exception("No page {} found".format(current_page + 1))

    # Div Ceiling - from http://stackoverflow.com/a/17511341
    window_mid = -(-window_size // 2)

    # Calculations to keep the current page the center page
    # on the pagination bar, until within window_mid elements
    # of either end of the pagination bar
    if total_pages <= window_size:
        start, stop = 1, total_pages + 1
        idx = current_page
    elif current_page <= window_mid - 1:
        start, stop = 1, window_size + 1
        idx = current_page
    elif current_page >= total_pages - window_mid:
        start, stop = total_pages - (window_size - 1), total_pages + 1
        idx = current_page - (total_pages - window_size)
    else:
        start, stop = current_page + 2 - window_mid, current_page + window_mid + 1
        idx = window_mid -1

    pages = [(i, '?{}={}{}'.format(param, i, frag)) for i in range(start, stop)]
    rows_ = [row_fmt(r) for r in rows[current_page*page_size : (current_page+1)*page_size]]

    return {
        'headers': headers,
        'rows': rows_,
        'pages': pages,
        'idx': idx,
    }

def make_perms_pagination(request, perms, name="Groups"):
    headers = ["Permitted " + name, "Permissions", "Actions"]
    link = '<a href="?rem_perms={}#Permissions">Remove All Permissions</a>'
    rows = [(r, p, link.format(r)) for r,p in perms]

    return make_pagination(request, headers, rows, param='page_perms', frag='#Permissions')

def make_metas_pagination(request, metas, name, meta_url):
    headers = [name + ' Meta Key', 'Actions']
    view_link = '<a href="{}?key={}">{}</a>'
    rem_link = '<a href="?rem_meta={}#Meta">Remove Meta Key</a>'
    fmt = lambda m: (view_link.format(meta_url, m, m), rem_link.format(m))

    return make_pagination(request, headers, metas, fmt, param='page_metas', frag='#Meta')
