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
import zlib
import io

from bosscore.request import BossRequest
from bosscore.error import BossParserError, BossError, ErrorCodes

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
            request_args = {
                "service": "cutout",
                "collection_name": parser_context['kwargs']['collection'],
                "experiment_name": parser_context['kwargs']['experiment'],
                "channel_name": parser_context['kwargs']['channel'],
                "resolution": parser_context['kwargs']['resolution'],
                "x_args": parser_context['kwargs']['x_range'],
                "y_args": parser_context['kwargs']['y_range'],
                "z_args": parser_context['kwargs']['z_range'],
            }
            if 't_range' in parser_context['kwargs']:
                request_args["time_args"] = parser_context['kwargs']['t_range']
            else:
                request_args["time_args"] = None

            req = BossRequest(parser_context['request'], request_args)
        except BossError as err:
            return BossParserError(err.message, err.error_code)
        except Exception as err:
            return BossParserError(str(err), ErrorCodes.UNHANDLED_EXCEPTION)

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossParserError("Unsupported data type provided to parser: {}".format(resource.get_data_type()),
                                   ErrorCodes.TYPE_ERROR)

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * bit_depth / 8
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossParserError("Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.",
                                   ErrorCodes.REQUEST_TOO_LARGE)

        try:
            # Decompress
            raw_data = blosc.decompress(stream.read())
            data_mat = np.fromstring(raw_data, dtype=resource.get_numpy_data_type())
        except MemoryError:
            return BossParserError("Ran out of memory decompressing data.",
                                    ErrorCodes.BOSS_SYSTEM_ERROR)
        except:
            return BossParserError("Failed to decompress data. Verify the datatype/bitdepth of your data "
                                   "matches the channel.", ErrorCodes.DATATYPE_DOES_NOT_MATCH)

        # Reshape and return
        try:
            if req.time_request:
                # Time series request (even if single time point) - Get 4D matrix
                parsed_data = np.reshape(data_mat,
                                         (len(req.get_time()),
                                          req.get_z_span(),
                                          req.get_y_span(),
                                          req.get_x_span()),
                                         order='C')
            else:
                # Not a time series request (time range [0,1] auto-populated) - Get 3D matrix
                parsed_data = np.reshape(data_mat, (req.get_z_span(), req.get_y_span(), req.get_x_span()), order='C')
        except ValueError:
            return BossParserError("Failed to unpack data. Verify the datatype of your POSTed data and "
                                   "xyz dimensions used in the POST URL.", ErrorCodes.DATA_DIMENSION_MISMATCH)

        return req, resource, parsed_data


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
            request_args = {
                "service": "cutout",
                "collection_name": parser_context['kwargs']['collection'],
                "experiment_name": parser_context['kwargs']['experiment'],
                "channel_name": parser_context['kwargs']['channel'],
                "resolution": parser_context['kwargs']['resolution'],
                "x_args": parser_context['kwargs']['x_range'],
                "y_args": parser_context['kwargs']['y_range'],
                "z_args": parser_context['kwargs']['z_range'],
            }
            if 't_range' in parser_context['kwargs']:
                request_args["time_args"] = parser_context['kwargs']['t_range']
            else:
                request_args["time_args"] = None

            req = BossRequest(parser_context['request'], request_args)
        except BossError as err:
            return BossParserError(err.message, err.status_code)
        except Exception as err:
            return BossParserError(str(err), ErrorCodes.UNHANDLED_EXCEPTION)

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossParserError("Unsupported data type provided to parser: {}".format(resource.get_data_type()),
                                   ErrorCodes.TYPE_ERROR)

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * bit_depth / 8
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossParserError("Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.",
                                   ErrorCodes.REQUEST_TOO_LARGE)

        # Decompress and return
        try:
            parsed_data = blosc.unpack_array(stream.read())
        except EOFError:
            return BossParserError("Failed to unpack data. Verify the datatype of your POSTed data and "
                                   "xyz dimensions used in the POST URL.", ErrorCodes.DATA_DIMENSION_MISMATCH)

        return req, resource, parsed_data


class NpygzParser(BaseParser):
    """
    Parser that handles npygz compressed binary data
    """
    media_type = 'application/npygz'

    def parse(self, stream, media_type=None, parser_context=None):
        """Method to decompress bytes from a POST that contains a gzipped npy saved numpy ndarray

        :param stream: Request stream
        stream type: django.core.handlers.wsgi.WSGIRequest
        :param media_type:
        :param parser_context:
        :return:
        """
        try:
            request_args = {
                "service": "cutout",
                "collection_name": parser_context['kwargs']['collection'],
                "experiment_name": parser_context['kwargs']['experiment'],
                "channel_name": parser_context['kwargs']['channel'],
                "resolution": parser_context['kwargs']['resolution'],
                "x_args": parser_context['kwargs']['x_range'],
                "y_args": parser_context['kwargs']['y_range'],
                "z_args": parser_context['kwargs']['z_range'],
            }
            if 't_range' in parser_context['kwargs']:
                request_args["time_args"] = parser_context['kwargs']['t_range']
            else:
                request_args["time_args"] = None

            req = BossRequest(parser_context['request'], request_args)
        except BossError as err:
            return BossParserError(err.message, err.status_code)
        except Exception as err:
            return BossParserError(str(err), ErrorCodes.UNHANDLED_EXCEPTION)

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossParserError("Unsupported data type provided to parser: {}".format(resource.get_data_type()),
                                   ErrorCodes.TYPE_ERROR)

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * bit_depth / 8
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossParserError("Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.",
                                   ErrorCodes.REQUEST_TOO_LARGE)

        # Decompress and return
        try:
            data_bytes = zlib.decompress(stream.read())

            # Open
            data_obj = io.BytesIO(data_bytes)
            parsed_data = np.load(data_obj)
        except EOFError:
            return BossParserError("Failed to unpack data. Verify the datatype of your POSTed data and "
                                   "xyz dimensions used in the POST URL.", ErrorCodes.DATA_DIMENSION_MISMATCH)

        return req, resource, parsed_data
