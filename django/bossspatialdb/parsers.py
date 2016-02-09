from rest_framework.parsers import BaseParser
import blosc


class BloscParser(BaseParser):
    """
    Parser that handles blosc compressed binary data
    """
    media_type = 'application/octet-stream'

    def parse(self, stream, media_type=None, parser_context=None):
        """
           Uncompressed bytes from a POST that contains blosc compressed matrix data

           **Bytes object produced should be C-ordered**

        :param stream: Request stream
        stream type: django.core.handlers.wsgi.WSGIRequest
        :param media_type:
        :param parser_context:
        :return:
        """
        # Decompress and return
        return blosc.decompress(stream.read())
