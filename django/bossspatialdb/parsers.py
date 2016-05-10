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

from rest_framework.parsers import BaseParser
import blosc
import numpy as np

from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError

import spdb


class BloscParser(BaseParser):
    """
    Parser that handles blosc compressed binary data
    """
    media_type = 'application/blosc'

    def parse(self, stream, media_type=None, parser_context=None):
        """Method to decompress bytes from a POST that contains blosc compressed matrix data

           **Bytes object decompressed should be C-ordered**

        :param stream: Request stream
        stream type: django.core.handlers.wsgi.WSGIRequest
        :param media_type:
        :param parser_context:
        :return:
        """
        # Process request and validate
        try:
            req = BossRequest(parser_context['request'])
        except BossError as err:
            return BossHTTPError(err.args[0], err.args[1], err.args[2])
#
        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)
#
        # Get datatype
        datatype = resource.get_data_type().lower()
        if datatype == "uint8":
            bitdepth = np.uint8
        elif datatype == "uint16":
            bitdepth = np.uint16
        elif datatype == "uint64":
            bitdepth = np.uint64
        else:
            return BossHTTPError(400, "Unsupported datatype provided to parser")

        # Decompress, reshape, and return
        raw_data = blosc.decompress(stream.read())
        data_mat = np.fromstring(raw_data, dtype=bitdepth)
        return np.reshape(data_mat, (req.get_z_span(), req.get_y_span(), req.get_x_span()), order='C')


class BloscPythonParser(BaseParser):
    """
    Parser that handles blosc compressed binary data in python numpy format
    """
    media_type = 'application/blosc-python'

    def parse(self, stream, media_type=None, parser_context=None):
        """Method to decompress bytes from a POST that contains blosc compressed numpy ndarray

        Only should be used if data sent was compressed using blosc.pack_array()

        :param stream: Request stream
        stream type: django.core.handlers.wsgi.WSGIRequest
        :param media_type:
        :param parser_context:
        :return:
        """
        # Decompress and return
        return blosc.unpack_array(stream.read())
