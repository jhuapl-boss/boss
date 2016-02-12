from django.http import JsonResponse
from bossutils.logger import BossLogger


class BossHTTPError(JsonResponse):
    """
    Custom HTTP Error class that logs and renders a json response

    When you reach a point in your code where you want to stop execution and return an error to the user:

        return BossHTTPError(409, 20001, "Key already exists")

    """

    def __init__(self, status, code, message):
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


