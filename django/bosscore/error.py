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

from django.http import JsonResponse
from bossutils.logger import BossLogger
from enum import IntEnum
import sys
import json


class ErrorCodes(IntEnum):
    """
    Enumeration of Error codes to support consistency
    """
    # Url Validation
    INVALID_URL = 1000
    INVALID_CUTOUT_ARGS = 1001
    TYPE_ERROR = 1002
    INVALID_POST_ARGUMENT = 1003
    UNABLE_TO_VALIDATE = 1004
    INVALID_ARGUMENT = 1005
    BAD_REQUEST = 1006

    # Request Validation
    REQUEST_TOO_LARGE = 2000
    DATATYPE_DOES_NOT_MATCH = 2001
    DATA_DIMENSION_MISMATCH = 2002
    DATATYPE_NOT_SUPPORTED = 2003
    INVALID_REQUEST = 2004
    UNSUPPORTED_4D = 2005

    # Unauthorized
    MISSING_ROLE = 3000
    MISSING_PERMISSION = 3001
    UNRECOGNIZED_PERMISSION = 3002
    INGEST_NOT_CREATOR = 3003

    # Database errors
    RESOURCE_NOT_FOUND = 4000
    GROUP_NOT_FOUND = 4001
    USER_NOT_FOUND = 4002
    INTEGRITY_ERROR = 4003
    OBJECT_NOT_FOUND = 4004
    RESOURCE_MARKED_FOR_DELETION = 4005

    # IO Errors
    IO_ERROR = 5000
    UNSUPPORTED_TRANSPORT_FORMAT = 5001
    SERIALIZATION_ERROR = 5002
    DESERIALIZATION_ERROR = 5003

    # Already exists
    GROUP_EXISTS = 6001
    RESOURCE_EXISTS = 6002

    # SSO Errors
    KEYCLOAK_EXCEPTION = 7001
    INVALID_ROLE = 7002

    # TO BE IMPLEMENTED
    FUTURE = 9000
    BOSS_SYSTEM_ERROR = 9001
    UNHANDLED_EXCEPTION = 9002
    UNSUPPORTED_VERSION = 9003



RESP_CODES = {

    ErrorCodes.INVALID_URL: 400,
    ErrorCodes.INVALID_CUTOUT_ARGS: 400,
    ErrorCodes.TYPE_ERROR: 400,
    ErrorCodes.INVALID_POST_ARGUMENT: 400,
    ErrorCodes.INVALID_ARGUMENT: 400,
    ErrorCodes.BAD_REQUEST: 400,
    ErrorCodes.UNABLE_TO_VALIDATE: 400,
    ErrorCodes.REQUEST_TOO_LARGE: 413,
    ErrorCodes.DATATYPE_DOES_NOT_MATCH: 400,
    ErrorCodes.DATA_DIMENSION_MISMATCH: 400,
    ErrorCodes.DATATYPE_NOT_SUPPORTED: 400,
    ErrorCodes.UNSUPPORTED_4D: 400,
    ErrorCodes.INVALID_REQUEST: 404,
    ErrorCodes.MISSING_ROLE: 403,
    ErrorCodes.MISSING_PERMISSION: 403,
    ErrorCodes.UNRECOGNIZED_PERMISSION: 404,
    ErrorCodes.INGEST_NOT_CREATOR: 403,
    ErrorCodes.RESOURCE_NOT_FOUND: 404,
    ErrorCodes.GROUP_NOT_FOUND: 404,
    ErrorCodes.USER_NOT_FOUND: 404,
    ErrorCodes.INTEGRITY_ERROR: 400,
    ErrorCodes.OBJECT_NOT_FOUND: 404,
    ErrorCodes.RESOURCE_MARKED_FOR_DELETION: 404,
    ErrorCodes.IO_ERROR: 404,
    ErrorCodes.UNSUPPORTED_TRANSPORT_FORMAT: 404,
    ErrorCodes.SERIALIZATION_ERROR: 404,
    ErrorCodes.DESERIALIZATION_ERROR: 404,
    ErrorCodes.GROUP_EXISTS: 404,
    ErrorCodes.RESOURCE_EXISTS: 404,
    ErrorCodes.KEYCLOAK_EXCEPTION: 500,
    ErrorCodes.INVALID_ROLE: 403,
    ErrorCodes.FUTURE: 404,
    ErrorCodes.BOSS_SYSTEM_ERROR: 400,
    ErrorCodes.UNHANDLED_EXCEPTION: 500,
    ErrorCodes.UNSUPPORTED_VERSION: 400

}


class BossError(Exception):
    """
    Custom Error class to capture the same information as a BossHTTPError

    When you reach a point in your code where you want to stop execution and return an error to the user:

        raise BossError("Key already exists", ErrorCodes.INVALID_REQUEST)

    """

    def __init__(self, *args):
        """
        Custom error class
        :param args: A tuple of (message, error_code)
        :return:
        """
        # Set status code
        if args[1] in RESP_CODES:
            self.status_code = RESP_CODES[args[1]]
        else:
            self.status_code = 400

        self.message = args[0]
        self.error_code = args[1]

    def to_http(self):
        """
        Convert error to an HTTP error so you can return to the user if in a view
        :return: bosscore.error.BossHTTPError
        """
        return BossHTTPError(self.message, self.error_code)


class BossParserError(object):
    """
    Custom Error class to capture the same information as a BossError without being an Exception so DRF doesn't empty
    the parsed response

    When you reach a point in a DRF parser where you want to stop execution and return an error to the user:

        return BossParserError("Key already exists", ErrorCodes.INVALID_REQUEST)

    In your view's POST handler you can then check if request.data is of type BossParserError and then return the error
    to the user if it is:

        if isinstance(request.data, BossParserError):
            return request.data.to_http()

    """

    def __init__(self, *args):
        """
        Custom HTTP error class
        :param args: A tuple of (message, error_code)
        :return:
        """
        # Set status code
        if args[1] in RESP_CODES:
            self.status_code = RESP_CODES[args[1]]
        else:
            self.status_code = 400

        self.message = args[0]
        self.error_code = args[1]

    def to_http(self):
        """
        Convert error to an HTTP error so you can return to the user if in a view
        :return: bosscore.error.BossHTTPError
        """
        return BossHTTPError(self.message, self.error_code)


class BossHTTPError(JsonResponse):
    """
    Custom HTTP Error class that logs and renders a json response

    When you reach a point in a django view where you want to stop execution and return an error to the user:

        return BossHTTPError("Key already exists", ErrorCodes.INVALID_REQUEST)

    """

    def __init__(self, message, code):
        """
        Custom HTTP error class
        :param status: HTTP Status code
        :type status: int
        :param code: An optional, arbitrary, and unique code to identify where the error was generated
        :type code: int
        :param message: Message to provide feedback to the user
        :return:
        """
        # Set status code
        self.status_code = RESP_CODES[code]

        # Log
        blog = BossLogger().logger
        blog.info("BossHTTPError - Status: {0} - Code: {1} - Message: {2}".format(self.status_code, code, message))

        # Return
        data = {'status': self.status_code, 'code': code, 'message': message}
        super(BossHTTPError, self).__init__(data)


class BossKeycloakError(JsonResponse):
    def __init__(self, message, code=ErrorCodes.KEYCLOAK_EXCEPTION):
        """
        Custom HTTP error class for converting a KeyCloakError exception into a JsonResponse

        Args:
            message (str): Error message to send back to user

        Note: If called in an exception handler, expects the exception to be a KeyCloakError
        """

        ex = sys.exc_info()[1]

        self.status_code = ex.status if ex else RESP_CODES[code]
        data = {
            'status': self.status_code,
            'code': ErrorCodes.KEYCLOAK_EXCEPTION,
            'message': message
        }

        if ex:
            if isinstance(ex.data, str):
                val = json.loads(ex.data)
            else:
                val = ex.data
            data.update(val)

        msg = "BossKeycloakError"
        for k in data:
            msg += " - {}: {}".format(k.capitalize(), data[k])

        log = BossLogger().logger
        log.info(msg)

        super(BossKeycloakError, self).__init__(data)


class BossResourceNotFoundError(BossHTTPError):
    """
    Custom HTTP Error class for Object not found errors
    """

    def __init__(self, object):
        """
        Custom HTTP Error class for object not found errors
        Args:
            object (str): Name of resource/object that user is trying to access/manipulate
        """
        super(BossResourceNotFoundError, self).__init__("{} does not exist.".format(object),
                                                        ErrorCodes.RESOURCE_NOT_FOUND)


class BossUserNotFoundError(BossHTTPError):
    """
    Custom HTTP Error class for Object not found errors
    """

    def __init__(self, object):
        """
        Custom HTTP Error class for object not found errors
        Args:
            object (str): Name of resource/object that user is trying to access/manipulate
        """
        super(BossUserNotFoundError, self).__init__("{} does not exist. Ensure that the user has logged in"
                                                    .format(object), ErrorCodes.USER_NOT_FOUND)


class BossGroupNotFoundError(BossHTTPError):
    """
    Custom HTTP Error class for Object not found errors
    """

    def __init__(self, object):
        """
        Custom HTTP Error class for object not found errors
        Args:
            object (str): Name of resource/object that user is trying to access/manipulate
        """
        super(BossGroupNotFoundError, self).__init__("{} does not exist.".format(object), ErrorCodes.GROUP_NOT_FOUND)


class BossPermissionError(BossHTTPError):
    """
    Custom HTTP Error class for permission based errors

    """

    def __init__(self, permission, object):
        """
        Custom HTTP Error class for permission based errors
        Args:
            permission (str): Name of missing permission that caused the error
            object (str): Name of resource that user is trying to access/manipulate
        """
        super(BossPermissionError, self).__init__("Missing {} permissions on the resource {}"
                                                  .format(permission, object), ErrorCodes.MISSING_PERMISSION)


class BossRestArgsError(BossHTTPError):
    """
    Custom HTTP Error class for Invalid rest args

    """

    def __init__(self, service, args):
        """
        Custom HTTP Error class for Invalid rest args
        Args:
            object (str): Name of resource/object that user is trying to access/manipulate
        """
        super(BossRestArgsError, self).__init__(RESP_CODES[ErrorCodes.INVALID_URL],
                                                "Invalid {} arguments in request {}.".format(service, args),
                                                ErrorCodes.INVALID_URL)
