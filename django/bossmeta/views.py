from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse, HttpResponseBadRequest

from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError, ErrorCodes
from . import metadb


class BossMeta(APIView):
    """
    View to handle read,write,update and delete metadata queries

    """

    def get(self, request, collection, experiment=None, channel=None):
        """
        View to handle GET requests for metadata

        Args:
            request: DRF Request object
            collection: Collection Name
            experiment: Experiment name. default = None
            channel: Channel name

        Returns:

        """
        print (collection)
        try:
            # Validate the request and get the lookup Key
            req = BossRequest(request)
            lookup_key = req.get_lookup_key()

        except BossError as err:
            return err.to_http()

        if not lookup_key or lookup_key == "":
            return BossHTTPError("Invalid request. Unable to parse the datamodel arguments", )

        if 'key' not in request.query_params:
            # List all keys that are valid for the query
            mdb = metadb.MetaDB()
            mdata = mdb.get_meta_list(lookup_key)
            keys = []
            if mdata:
                for meta in mdata:
                    keys.append(meta['key'])
            data = {'keys': keys}
            return Response(data)

        else:

            mkey = request.query_params['key']
            mdb = metadb.MetaDB()
            mdata = mdb.get_meta(lookup_key, mkey)
            if mdata:
                data = {'key': mdata['key'], 'value': mdata['metavalue']}
                return Response(data)
            else:
                return BossHTTPError("Invalid request. Key {} Not found in the database".format(mkey),
                                     ErrorCodes.INVALID_POST_ARGUMENT)

    def post(self, request, collection, experiment=None, channel=None):
        """
        View to handle POST requests for metadata

        Args:
            request: DRF Request object
            collection: Collection Name specifying the collection you want to get the meta data for
            experiment: Experiment name. default = None
            channel: Channel name. Default = None

        Returns:

        """

        if 'key' not in request.query_params or 'value' not in request.query_params:
            return BossHTTPError("Missing optional argument key/value in the request", ErrorCodes.INVALID_POST_ARGUMENT)

        try:
            req = BossRequest(request)
            lookup_key = req.get_lookup_key()
        except BossError as err:
            return err.to_http()

        if not lookup_key:
            return BossHTTPError("Invalid request. Unable to parse the datamodel arguments",
                                 ErrorCodes.INVALID_POST_ARGUMENT)

        mkey = request.query_params['key']
        value = request.query_params['value']

        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB()
        if mdb.get_meta(lookup_key, mkey):
            return BossHTTPError("Invalid request. The key {} already exists".format(mkey),
                                 ErrorCodes.INVALID_POST_ARGUMENT)
        mdb.write_meta(lookup_key, mkey, value)
        return HttpResponse(status=201)

    def delete(self, request, collection, experiment=None, channel=None):
        """
        View to handle the delete requests for metadata
        Args:
            request: DRF Request object
            collection: Collection name. Default = None
            experiment: Experiment name. Default = None
            channel: Channel name . Default = None

        Returns:

        """

        if 'key' not in request.query_params:
            return BossHTTPError("Missing optional argument key in the request", ErrorCodes.INVALID_POST_ARGUMENT)

        try:
            req = BossRequest(request)
            lookup_key = req.get_lookup_key()
        except BossError as err:
            return err.to_http()

        if not lookup_key:
            return BossHTTPError("Invalid request. Unable to parse the datamodel arguments",
                                 ErrorCodes.INVALID_POST_ARGUMENT)

        mkey = request.query_params['key']

        # Delete metadata from the dynamodb database
        mdb = metadb.MetaDB()
        response = mdb.delete_meta(lookup_key, mkey)

        if 'Attributes' in response:
            return HttpResponse(status=200)
        else:
            return BossHTTPError("[ERROR]- Key {} not found ".format(mkey), ErrorCodes.INVALID_POST_ARGUMENT)

    def put(self, request, collection, experiment=None, channel=None):
        """
        View to handle update requests for metadata
        Args:
            request: DRF Request object
            collection: Collection Name. Default = None
            experiment: Experiment Name. Default = None
            channel: Channel Name Default + None

        Returns:

        """

        if 'key' not in request.query_params or 'value' not in request.query_params:
            return BossHTTPError("Missing optional argument key/value in the request",
                                 ErrorCodes.INVALID_POST_ARGUMENT)

        try:
            req = BossRequest(request)
            lookup_key = req.get_lookup_key()
        except BossError as err:
            return err.to_http()

        if not lookup_key:
            return BossHTTPError("Invalid request. Unable to parse the datamodel arguments",
                                 ErrorCodes.INVALID_POST_ARGUMENT)

        mkey = request.query_params['key']
        value = request.query_params['value']

        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB()
        if not mdb.get_meta(lookup_key, mkey):
            return BossHTTPError("Invalid request. The key {} does not exists".format(mkey),
                                 ErrorCodes.INVALID_POST_ARGUMENT)
        mdb.update_meta(lookup_key, mkey, value)
        return HttpResponse(status=200)
