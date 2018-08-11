import datetime as dt

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Info, User, Encoding, SensorData, Log
from .serializers import InfoSerializer, UserSerializer, EncodingSerializer, SensorDataSerializer, \
    LogSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API for users registered by face recognition
    retrieve:
        Return user information.

    list:
        Return all users, ordered by most recently joined.

    create:
        Create a new user.

    delete:
        Remove an existing user.

    partial_update:
        Update one or more fields on an existing user.

    update:
        Update a user.

    encodings:
        Return encodings of specific user
    """
    def delete(self, request):
        pass
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # @action(methods=['get'], detail=True, url_path='pictures', url_name='pictures')
    def encodings(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
            encodings = Encoding.objects.filter(user_id=pk)
            serializer = EncodingSerializer(encodings, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class InfoViewSet(viewsets.ModelViewSet):
    """
    API for storing and retrieving general information
    retrieve:
        Return a information.

    list:
        Return all information.

    create:
        Create a new information.

    delete:
        Remove an existing information.

    partial_update:
        Update one or more fields on an existing information.

    update:
        Update a information.
    """
    queryset = Info.objects.all()
    serializer_class = InfoSerializer


class EncodingViewSet(viewsets.ModelViewSet):
    """
    API for storing and retrieving general encoding
    retrieve:
        Return a encoding.

    list:
        Return all encodings.

    create:
        Create a new encoding.

    delete:
        Remove an existing encoding.

    partial_update:
        Update one or more fields on an existing encoding.

    update:
        Update a encoding.
    """
    queryset = Encoding.objects.all()
    serializer_class = EncodingSerializer


class SensorDataViewSet(viewsets.ModelViewSet):
    """
    API for storing and retrieving sensor information
    retrieve:
        Return a sensor information.

    list:
        Return all sensor information.

    create:
        Create a new sensor information.

    delete:
        Remove an existing sensor information.

    partial_update:
        Update one or more fields on an existing sensor information.

    update:
        Update a sensor information.

    last:
        Return the last sensor information of the type defined (all by default)

    time_range:
        Return  all sensor information created on the time range of the type (all by default) defined
    """
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer

    def list(self, request, t_type=None):
        if t_type:
            sensors = SensorData.objects.filter(type=t_type)

        else:
            sensors = self.queryset
        serializer = self.get_serializer(sensors, many=True)
        return Response(serializer.data)

    def last(self, request, t_type=None):
        try:
            if t_type:
                sensor = SensorData.objects.filter(type=t_type).latest('created')
            else:
                sensor = SensorData.objects.latest('created')
            serializer = SensorDataSerializer(sensor)
            return Response(serializer.data)
        except SensorData.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def time_range(self, request, t_from, t_to, t_type=None):
        try:
            t_from = dt.datetime.fromtimestamp(float(t_from))
            t_to = dt.datetime.fromtimestamp(float(t_to))
            if t_type:
                sensors = SensorData.objects.filter(type=t_type)
                sensors = sensors.filter(created__range=(t_from, t_to))
            else:
                sensors = SensorData.objects.filter(created__range=(t_from, t_to))
            serializer = SensorDataSerializer(sensors, many=True)
            return Response(serializer.data)
        except SensorData.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class LogViewSet(viewsets.ModelViewSet):
    """
    API for storing and retrieving logs
    retrieve:
        Return a log.

    list:
        Return all logs.

    create:
        Create a new log.

    delete:
        Remove an existing log.

    partial_update:
        Update one or more fields on an existing log.

    update:
        Update a log.
    """
    queryset = Log.objects.all()
    serializer_class = LogSerializer
