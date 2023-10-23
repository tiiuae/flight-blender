from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from conftest import get_oauth2_token
from unittest.mock import patch
import unittest
from .views import _fetch_weather_data
from .weather_service import WeatherService
import time


JWT = get_oauth2_token()


# Create your tests here.
class WeatherMonitoringOperationsTestCase(APITestCase):
    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
        self.api_url = reverse("get_weather_data")

    @patch("requests.get")
    def test_get_weather(self, mock_get):
        mock_response = {
            "weather": "sunny",
            "temperature": "70",
            "wind_speed": "10",
            "wind_direction": "N",
            "precipitation": "0",
            "visibility": "10",
            "cloud_coverage": "0",
        }

        mock_get.return_value.status_code = status.HTTP_200_OK
        mock_get.return_value.json.return_value = mock_response
        response = self.client.get(self.api_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertJSONEqual(response.content, mock_response)


class WeatherServiceTestCase(unittest.TestCase):
    def test_get_weather_data(self):
        weather_service = WeatherService(
            api_url="https://api.open-meteo.com/v1/forecast"
        )
        longitude = 24.4512
        latitude = 54.397
        current_time = time.time()
        timezone = "UTC"
        hourly_data = [
            "temperature_2m",
            "showers",
            "windspeed_10m",
            "winddirection_10m",
            "windgusts_10m",
        ]

        weather_data = weather_service.get_weather_data(
            longitude, latitude, current_time, timezone, hourly_data
        )

        self.assertTrue(bool(weather_data))
