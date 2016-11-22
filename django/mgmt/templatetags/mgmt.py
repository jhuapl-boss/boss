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

