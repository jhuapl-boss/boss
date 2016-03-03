from django.http import JsonResponse
from bossutils.logger import BossLogger


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
        blog = BossLogger()
        blog.info("BossHTTPError - Status: {0} - Code: {1} - Message: {2}".format(status, code, message))

        # Return
        data = {'status': status, 'code': code, 'message': message}
        super(BossHTTPError, self).__init__(data)


