from django import template

register = template.Library()

@register.simple_tag
def mgmt_url(base, **kwargs):
    """Join a base url with url parameters

    Used to help pass a url a function like add_modal

    Args:
        base (string) : Base url string (already resolved by Django)
        kwargs (dict) : Key value url parameters to append
    """
    params = "&".join(["{}={}".format(k,v) for k,v in kwargs.items()])
    return "?".join((base, params))

@register.inclusion_tag("add_modal.html")
def add_modal(form, error, name, url):
    """Render the given template to provide a modal dialog
    that provides a popup form.

    Args:
        form (Forms) : Django form to render
        error (String) : String to add to the form's class attribute
        name (String) : Name of the buttons / modal
        url (String) : URL to post the form to
    """
    return {
        'form': form,
        'error': error,
        'name': name,
        'id': name.replace(' ', ''),
        'url': url
    }

@register.inclusion_tag("meta_modal.html")
def add_meta_modal():
    """Render the given template to provide a modal dialog
    that provides a popup display of metadata
    """
    return {}

@register.inclusion_tag("update_form.html")
def update_form(form, error, name, url, **kwargs):
    """Render the given template to provide an update form

    Args:
        form (Forms) : Django form to render
        error (String) : String to add to the form's class attribute
        name (String) : Name of the buttons / modal
        url (String) : URL to post the form to
        kwargs (dict) : (Optional) Additional rows to add to the top of the form
    """
    return {
        'form': form,
        'error': error,
        'name': name,
        'id': name.replace(' ', ''),
        'url': url,
        'headers': kwargs.items()
    }

@register.inclusion_tag("table.html")
def paginated_table(kwargs):
    """Display a paginated table

    Args:
        kwargs (dict): Dictionary with the following arguments defined
            headers (list): List of header columns for the table
            rows (list): List of rows, which are lists of columns matching headers
            pages (list): List of (name, url) for each pagination link to display
            idx (int): Index of the current page in pages list
    """
    headers = kwargs['headers']
    rows = kwargs['rows']
    pages = kwargs['pages']
    idx = kwargs['idx']

    is_first = idx == 0
    is_last = idx == len(pages) - 1

    prev_class = "disabled" if is_first else ""
    prev_url = "" if is_first else pages[idx - 1][1]
    next_class = "disabled" if is_last else ""
    next_url = "" if is_last else pages[idx + 1][1]

    pages = [("active" if i == idx else "", pages[i][0], pages[i][1]) for i in range(len(pages))]

    return {
        'headers': headers,
        'rows': rows,
        'show_pagination': len(pages) != 1, # Only show the bar if multiple pages
        'pages': pages,
        'previous_class': prev_class,
        'previous_url': prev_url,
        'next_class': next_class,
        'next_url': next_url,
    }

@register.inclusion_tag("breadcrumb.html")
def breadcrumb(*args):
    """"Render a breadcrumb trail

    Args:
        args (list) : list of urls and url name followed by the final name
                      Example: url1, name1, url2, name2, name3
    """
    def pairs(l):
        a = iter(l)
        return list(zip(a,a))

    return {
        'urls': pairs(args[:-1]),
        'page': args[-1]
    }

