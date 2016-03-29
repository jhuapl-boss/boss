from rest_framework import renderers
import blosc


class BloscPythonRenderer(renderers.BaseRenderer):
    """ A DRF renderer for a blosc encoded cube of data using the numpy inteface

    Should only be used by applications written in python
    """
    media_type = 'application/blosc-python'
    format = 'bin'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return blosc.pack_array(data.data)


class BloscRenderer(renderers.BaseRenderer):
    """ A DRF renderer for a blosc encoded cube of data

    Should only be used by applications written in python
    """
    media_type = 'application/blosc-python'
    format = 'bin'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return blosc.compress(data.data, typesize=data.bitdepth)
