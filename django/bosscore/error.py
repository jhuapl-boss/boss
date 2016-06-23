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


class ErrorCodes(IntEnum):
    """
    Enumeration of Error codes to support consistency
    """
    # Url Validation
    INVALID_URL = 1000
    INVALID_CUTOUT_ARGS = 1001

    # Privileges
    MISSING_PRIVILEGE = 2000

    # Permissions
    MISSING_PERMISSION = 3000

    # Object Not Found
    OBJECT_NOT_FOUND = 4000

    # IO Errors
    IO_ERROR = 5000
    UNSUPPORTED_TRANSPORT_FORMAT = 5001
    SERIALIZATION_ERROR = 5002
    DESERIALIZATION_ERROR = 5003


class BossError(Exception):
    """
    Custom Error class to capture the same information as a BossHTTPError

    When you reach a point in your code where you want to stop execution and return an error to the user:

        raise BossError(409, "Key already exists", 20001)

    """

    def __init__(self, *args):
        """
        Custom HTTP error class
        :param args: A tuple of (http_status_code, message, error_code)
        :return:
        """
        # Set status code
        self.args = args

        if len(args) == 2:
            temp = list(args)
            temp.append(0)
            self.args = tuple(temp)

    def to_http(self):
        """
        Convert error to an HTTP error so you can return to the user if in a view
        :return: bosscore.error.BossHTTPError
        """
        return BossHTTPError(self.args[0], self.args[1], self.args[2])


class BossParserError(object):
    """
    Custom Error class to capture the same information as a BossError without being an Exception so DRF doesn't empty
    the parsed response

    When you reach a point in a DRF parser where you want to stop execution and return an error to the user:

        return BossParserError(409, "Key already exists", 20001)

    In your view's POST handler you can then check if request.data is of type BossParserError and then return the error
    to the user if it is:

        if isinstance(request.data, BossParserError):
            return request.data.to_http()

    """

    def __init__(self, *args):
        """
        Custom HTTP error class
        :param args: A tuple of (http_status_code, message, error_code)
        :return:
        """
        # Set status code
        self.args = args

        if len(args) == 2:
            temp = list(args)
            temp.append(0)
            self.args = tuple(temp)

    def to_http(self):
        """
        Convert error to an HTTP error so you can return to the user if in a view
        :return: bosscore.error.BossHTTPError
        """
        return BossHTTPError(self.args[0], self.args[1], self.args[2])


class BossHTTPError(JsonResponse):
    """
    Custom HTTP Error class that logs and renders a json response

    When you reach a point in a django view where you want to stop execution and return an error to the user:

        return BossHTTPError(409, 20001, "Key already exists")

    """

    def __init__(self, status, message, code=0):
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
        self.status_code = status

        # Log
        blog = BossLogger().logger
        blog.info("BossHTTPError - Status: {0} - Code: {1} - Message: {2}".format(status, code, message))

        # Return
        data = {'status': status, 'code': code, 'message': message}
        super(BossHTTPError, self).__init__(data)
     
        
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
        super(BossPermissionError, self).__init__(403,
                                                  "Missing {} permissions on the resource {}".format(permission,
                                                                                                     object),
                                                  ErrorCodes.MISSING_PERMISSION)




