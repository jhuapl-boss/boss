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

from rest_framework import renderers
import blosc
import numpy as np


class BloscPythonRenderer(renderers.BaseRenderer):
    """ A DRF renderer for a blosc encoded cube of data using the numpy interface

    Should only be used by applications written in python
    """
    media_type = 'application/blosc-python'
    format = 'bin'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):

        if not data.data.flags['C_CONTIGUOUS']:
            data.data = data.data.copy(order='C')

        # Return data, squeezing time dimension if only a single point
        try:
            return blosc.pack_array(np.squeeze(data.data, axis=(0,)))
        except ValueError:
            # The are more than 1 time points so don't squeeze.
            return blosc.pack_array(data.data)


class BloscRenderer(renderers.BaseRenderer):
    """ A DRF renderer for a blosc encoded cube of data

    """
    media_type = 'application/blosc'
    format = 'bin'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):

        if not data.data.flags['C_CONTIGUOUS']:
            data.data = data.data.copy(order='C')

        # Return data, squeezing time dimension if only a single point
        try:
            return blosc.compress(np.squeeze(data.data, axis=(0,)), typesize=renderer_context['view'].bit_depth)
        except ValueError:
            # The are more than 1 time points so don't squeeze.
            return blosc.compress(data.data, typesize=renderer_context['view'].bit_depth)

