from datetime import datetime

from django.http import JsonResponse
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file as oauth_file, client, tools
from rest_framework import viewsets
from rest_framework.response import Response

from memory.models import SensorData
from .constants import TZ_DEFAULT, LATITUDE_DEFAULT, LONGITUDE_DEFAULT, SPREADSHEET_ID, RANGE_NAME, GOOGLE_SHEET_SCOPES
from .helpers import get_weather
from .models import Notification
from .serializers import NotificationSerializer

google_sheet_service = None

def initGoogleSheetEngine():
    global google_sheet_service
    if not google_sheet_service:
        store = oauth_file.Storage('res/credentials/token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('res/credentials/google.json', GOOGLE_SHEET_SCOPES)
            creds = tools.run_flow(flow, store)
        google_sheet_service = build('sheets', 'v4', http=creds.authorize(Http()), cache_discovery=False)

def notifications_process():
    global google_sheet_service
    # Rules engine
    notifications = []
    latest_temp_obj = None
    latest_humidity_obj = None
    try:
        latest_temp_obj = SensorData.objects.filter(type="temperature").latest('created')
    except:
        pass
    try:
        latest_humidity_obj = SensorData.objects.filter(type="humidity").latest('created')
    except:
        pass

    # Dates
    actual_date = datetime.now(tz=TZ_DEFAULT)
    today = datetime(actual_date.year, actual_date.month, actual_date.day, tzinfo=TZ_DEFAULT)
    tomorrow = datetime(year=actual_date.year, month=actual_date.month, day=actual_date.day + 1,
                        hour=actual_date.hour, tzinfo=TZ_DEFAULT)
    # Memorized information

    date = latest_temp_obj.created
    weather_info_tomorrow = get_weather(latitude=LATITUDE_DEFAULT, longitude=LONGITUDE_DEFAULT,
                                        time=tomorrow.timestamp(),
                                        language='fr')
    if latest_temp_obj:
        latest_temperature = float(latest_temp_obj.data)
        # Rule n°1 : temperature is recent and greater than 25°C
        if date > today and latest_temperature >= 25:
            notifications.append({'type': 'message', 'target': 'all',
                                  'data': 'La temperature est de {:.0f}°C. Pensez à bien vous hydrater !'.format(
                                      latest_temperature)})
        # Rule n° 2 : temperature is recent and lower than 20°C
        if date > today and latest_temperature <= 20:
            notifications.append({'type': 'message', 'target': 'all',
                                  'data': 'La temperature est de {:.0f}°C. Pensez à bien vous couvrir et de boir un café bien chaud !'.format(
                                      latest_temperature)})
    if latest_humidity_obj:
        latest_humidity = float(latest_humidity_obj.data)
        # Rule n° 3 : humidity is recent and greater than 80%
        if date > today and latest_humidity >= 80:
            notifications.append({'type': 'message', 'target': 'all',
                                  'data': "L'humidité est de {}%. N'hésitez pas à vous dégourdir les jambes !".format(
                                      latest_humidity)})
        # Rule n° 4 : humidity is recent and lower than 20%
        if date > today and latest_humidity <= 20:
            notifications.append({'type': 'message', 'target': 'all',
                                  'data': "L'humidité est de {}%. Hydratez vous bien la peau et aérez la pièce.".format(
                                      latest_humidity)})
    # Rule n° 5 : Tomorrow is raining
    if weather_info_tomorrow:
        if weather_info_tomorrow['daily']['precipProbability'] >= 0.45 and weather_info_tomorrow['daily'].get(
                'precipType') == 'rain' and weather_info_tomorrow['daily'].get('precipIntensityMax') > 0.5:
            precip_max_time = datetime.fromtimestamp(weather_info_tomorrow['daily']['precipIntensityMaxTime'],
                                                     tz=TZ_DEFAULT)
            notifications.append({'type': 'message', 'target': 'all',
                                  'data': "Attention ! Demain il risque de pleuvoir aux alentours de {:02d}h{:02d} ! N'oubliez pas votre parapluie.".format(
                                      precip_max_time.hour, precip_max_time.minute)})

    # Rule n° 6 : Tomorrow is full moon
    if weather_info_tomorrow:
        if 0.45 <= weather_info_tomorrow['daily'].get('moonPhase') <= 0.55:
            notifications.append({'type': 'message', 'target': 'all',
                                  'data': "Demain c'est la pleine lune. N'oubliez pas votre appareil photo ;)"})

    # Rule n°7 : Google Sheet
    try:
        initGoogleSheetEngine()
        result = google_sheet_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME).execute()
        values = result.get('values', [])
        if values:
            for value in values:
                if len(value) > 1:
                    identity = value[1]
                else:
                    identity = "Anonyme"
                notifications.append({'type': 'message', 'target': 'all',
                                      'data': "{} : {}".format(identity, value[0])})
    except Exception as e:
        print('Google Sheets error : {}'.format(e))
        pass
    return notifications

class NotificationViewSet(viewsets.ModelViewSet):
    """
    API for notifications
    get_notifications:
        Get the notifications

    expiration:
        Expire a notification

    """

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer



    def get_notifications(self, request=None):
        notifications = notifications_process()
        return JsonResponse(notifications, safe=False)

    def expiration(self, request):
        return Response('WIP')


