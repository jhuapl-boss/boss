from rest_framework import renderers
import blosc
import numpy as np
from django.http import HttpResponse

from bosscore.error import BossHTTPError

# TODO: Look into why renderers aren't getting called properly. Currently pass-throughs so you don't get 406 errors

class BloscPythonRenderer(renderers.BaseRenderer):
    """ A DRF renderer for a blosc encoded cube of data using the numpy inteface

    Should only be used by applications written in python
    """
    media_type = 'application/blosc-python'
    format = 'bin'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        #return blosc.pack_array(data.data)
        pass

class BloscRenderer(renderers.BaseRenderer):
    """ A DRF renderer for a blosc encoded cube of data

    """
    media_type = 'application/blosc'
    format = 'bin'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):

        #if renderer_context['view'].data_type == "uint8":
        #    bitdepth = 8
        #elif renderer_context['view'].data_type == "uint32":
        #    bitdepth = 32
        #elif renderer_context['view'].data_type == "uint64":
        #    bitdepth = 64
        #else:
        #    return BossHTTPError(400, "Unsupported datatype provided to parser")
#
        ## TODO: Look into this extra copy.  Probably can ensure ndarray is c-order when created.
        #if not data.flags['C_CONTIGUOUS']:
        #    data = data.copy(order='C')
#
        #compressed_data = blosc.compress(data, typesize=bitdepth)
        #return Response(compressed_data, content_type='application/blosc')
        pass
