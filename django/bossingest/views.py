from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework import generics
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer


from .serializers import IngestSchemaListSerializer, IngestSchemaCreateSerializer
from .models import IngestSchema


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS or
            request.user and
            request.user.is_staff
        )


class IngestSchemaListView(generics.ListCreateAPIView):
    """
    Endpoint to list ingest schemas

    * Only administrators can add new schemas
    """
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (IsAdminOrReadOnly,)

    model = IngestSchema
    queryset = IngestSchema.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IngestSchemaCreateSerializer
        return IngestSchemaListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        item = IngestSchema.objects.create(name=serializer.data['name'],
                                           version=serializer.data['version'],
                                           schema=serializer.data['schema'],
                                           deprecated=serializer.data['deprecated'])

        result = IngestSchemaCreateSerializer(item)
        return Response(result.data, status=status.HTTP_201_CREATED)


class MultipleFieldLookupMixin(object):
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        queryset = self.get_queryset()             # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {}
        for field in self.lookup_fields:
            filter[field] = self.kwargs[field]
        return get_object_or_404(queryset, **filter)  # Lookup the object


class IngestSchemaView(MultipleFieldLookupMixin, generics.RetrieveAPIView):
    """
    View to list all users in the system.

    """
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.TokenAuthentication,)
    permission_classes = (IsAdminOrReadOnly,)

    queryset = IngestSchema.objects.all()
    serializer_class = IngestSchemaCreateSerializer
    lookup_fields = ('name', 'version')


class IngestJobView(APIView):
    """
    View to handle creating, joining, and deleting ingest jobs
    """
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.TokenAuthentication,)

    def __init__(self):
        super().__init__()

    def get(self, ingest_job_id):
        """

        Args:
            ingest_job_id:

        Returns:

        """


        # Send data to renderer
        return Response({})

    def post(self, config_data):
        """

        Args:
            config_data:

        Returns:

        """

        # Send data to renderer
        return Response({})

    def delete(self, ingest_job_id):
        """

        Args:
            config_data:

        Returns:

        """

        # Send data to renderer
        return Response({})
