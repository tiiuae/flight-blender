from django.http import JsonResponse
from rest_framework.decorators import api_view
from auth_helper.utils import requires_scopes
from unittest.mock import patch
from .weather_service import WeatherService
import time


@api_view(["GET"])
@requires_scopes(["blender.read"])
def get_weather_data(request):
    data = _fetch_weather_data()

    return JsonResponse(data, safe=False)


def _fetch_weather_data():
    # weather_data_response = requests.get(
    #     "https://api.open-meteo.com/v1/forecast?latitude=24.4512&longitude=54.397&hourly=temperature_2m&forecast_days=1"
    # )

    weather_service = WeatherService("https://api.open-meteo.com/v1/forecast")

    weather_data_response = weather_service.get_weather_data(
        24.4512,
        54.397,
        time.time(),
        "UTC",
        [
            "temperature_2m",
            "showers",
            "windspeed_10m",
            "winddirection_10m",
            "windgusts_10m",
        ],
    )

    return weather_data_response
