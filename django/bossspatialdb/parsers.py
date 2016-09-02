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
from django.conf import settings

import blosc
import numpy as np

from bosscore.request import BossRequest
from bosscore.error import BossParserError, BossError

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
            return BossParserError(err.args[0], err.args[1], err.args[2])

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossParserError(400, "Unsupported data type provided to parser: {}".format(resource.get_data_type()))

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * bit_depth / 8
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossParserError(413, "Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.")

        try:
            # Decompress
            raw_data = blosc.decompress(stream.read())
            data_mat = np.fromstring(raw_data, dtype=resource.get_numpy_data_type())
        except:
            return BossParserError(400, "Failed to decompress data. Verify the datatype/bitdepth of your data "
                                        "matches the channel/layer.")

        # Reshape and return
        try:
            if len(req.get_time()) > 1:
                # Time series data
                return np.reshape(data_mat, (len(req.get_time()), req.get_z_span(), req.get_y_span(), req.get_x_span()),
                                  order='C')
            else:
                return np.reshape(data_mat, (req.get_z_span(), req.get_y_span(), req.get_x_span()), order='C')
        except ValueError:
            return BossParserError(400, "Failed to unpack data. Verify the datatype of your POSTed data and "
                                   "xyz dimensions used in the POST URL.")


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
        try:
            req = BossRequest(parser_context['request'])
        except BossError as err:
            return BossParserError(err.args[0], err.args[1], err.args[2])

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossParserError(400,
                                   "Unsupported data type provided to parser: {}".format(resource.get_data_type()))

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * bit_depth / 8
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossParserError(413, "Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.")

        # Decompress and return
        try:
            return blosc.unpack_array(stream.read())
        except EOFError:
            return BossParserError(400, "Failed to unpack data. Verify the datatype of your POSTed data and "
                                   "xyz dimensions used in the POST URL.")

