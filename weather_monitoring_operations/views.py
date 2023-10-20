import requests
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view

from auth_helper.utils import requires_scopes


@api_view(["GET"])
@requires_scopes(["blender.read"])
def get_weather_data(request):
    data = _fetch_weather_data()

    return JsonResponse(data, safe=False)


def _fetch_weather_data():
    weather_data_response = requests.get(
        "https://api.open-meteo.com/v1/forecast?latitude=24.4512&longitude=54.397&hourly=temperature_2m&forecast_days=1"
    )

    if weather_data_response.status_code == status.OK:
        return weather_data_response.json()
    else:
        raise Exception("Error fetching weather data")
