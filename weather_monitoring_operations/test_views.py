import time
import unittest
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from conftest import get_oauth2_token

JWT = get_oauth2_token()


# Create your tests here.
class WeatherMonitoringOperationsTests(APITestCase):
    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
        self.api_url = reverse("weather")

    def test_get_weather_no_longitude_param(self):
        response = self.client.get(
            self.api_url,
            content_type="application/json",
        )
        self.assertEqual(response.json(), {"error": "Longitude parameter is required"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_weather_no_latitude_param(self):
        response = self.client.get(
            self.api_url + "?longitude=100.01",
            content_type="application/json",
        )
        self.assertEqual(response.json(), {"error": "Latitude parameter is required"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("requests.get")
    def test_get_weather_unexpected_json_response_from_service(self, mock_get):
        mock_unexpected_json_response = {
            "weather": "sunny",
            "temperature": "70",
            "wind_speed": "10",
            "wind_direction": "N",
            "precipitation": "0",
            "visibility": "10",
            "cloud_coverage": "0",
        }
        mock_get.return_value.status_code = status.HTTP_200_OK
        mock_get.return_value.json.return_value = mock_unexpected_json_response
        response = self.client.get(
            self.api_url + "?longitude=100.01&latitude=100.02",
            content_type="application/json",
        )

        self.assertEqual(
            response.json(),
            {
                "latitude": ["This field is required."],
                "longitude": ["This field is required."],
                "generationtime_ms": ["This field is required."],
                "utc_offset_seconds": ["This field is required."],
                "timezone": ["This field is required."],
                "timezone_abbreviation": ["This field is required."],
                "elevation": ["This field is required."],
                "hourly_units": ["This field is required."],
                "hourly": ["This field is required."],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("requests.get")
    def test_get_weather_valid_json_response_from_service(self, mock_get):
        mock_valid_json_response = {
            "latitude": 54.375,
            "longitude": 24.4375,
            "generationtime_ms": 0.03504753112792969,
            "utc_offset_seconds": 0,
            "timezone": "Coordinated Universal Time",
            "timezone_abbreviation": "UTC",
            "elevation": 129.0,
            "hourly_units": {
                "time": "iso8601",
                "temperature_2m": "°C",
                "showers": "mm",
                "windspeed_10m": "km/h",
                "winddirection_10m": "°",
                "windgusts_10m": "km/h",
            },
            "hourly": {
                "time": [
                    "2023-11-10T00:00",
                    "2023-11-10T01:00",
                    "2023-11-10T02:00",
                    "2023-11-10T03:00",
                    "2023-11-10T04:00",
                    "2023-11-10T05:00",
                    "2023-11-10T06:00",
                    "2023-11-10T07:00",
                    "2023-11-10T08:00",
                    "2023-11-10T09:00",
                    "2023-11-10T10:00",
                    "2023-11-10T11:00",
                    "2023-11-10T12:00",
                    "2023-11-10T13:00",
                    "2023-11-10T14:00",
                    "2023-11-10T15:00",
                    "2023-11-10T16:00",
                    "2023-11-10T17:00",
                    "2023-11-10T18:00",
                    "2023-11-10T19:00",
                    "2023-11-10T20:00",
                    "2023-11-10T21:00",
                    "2023-11-10T22:00",
                    "2023-11-10T23:00",
                ],
                "temperature_2m": [
                    5.7,
                    5.5,
                    5.1,
                    4.6,
                    4.1,
                    3.7,
                    3.5,
                    3.8,
                    4.7,
                    5.8,
                    6.6,
                    7.1,
                    7.4,
                    7.2,
                    6.8,
                    6.0,
                    5.6,
                    5.4,
                    5.4,
                    5.4,
                    5.5,
                    5.4,
                    5.4,
                    5.4,
                ],
                "showers": [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                "windspeed_10m": [
                    11.8,
                    12.1,
                    11.5,
                    11.3,
                    11.5,
                    12.2,
                    12.2,
                    12.2,
                    12.2,
                    12.8,
                    12.8,
                    12.0,
                    12.2,
                    11.3,
                    11.0,
                    9.1,
                    9.3,
                    9.7,
                    9.0,
                    8.6,
                    8.0,
                    8.0,
                    8.4,
                    8.3,
                ],
                "winddirection_10m": [
                    168,
                    168,
                    166,
                    163,
                    166,
                    166,
                    166,
                    166,
                    166,
                    170,
                    170,
                    164,
                    161,
                    153,
                    157,
                    162,
                    152,
                    158,
                    164,
                    165,
                    162,
                    153,
                    149,
                    146,
                ],
                "windgusts_10m": [
                    27.7,
                    27.0,
                    26.6,
                    26.3,
                    26.3,
                    27.4,
                    28.1,
                    28.1,
                    28.1,
                    29.9,
                    29.9,
                    29.2,
                    28.1,
                    28.1,
                    25.6,
                    24.5,
                    20.5,
                    21.2,
                    21.2,
                    19.8,
                    18.7,
                    18.0,
                    19.1,
                    18.7,
                ],
            },
        }

        mock_get.return_value.status_code = status.HTTP_200_OK
        mock_get.return_value.json.return_value = mock_valid_json_response
        response = self.client.get(
            self.api_url + "?longitude=100.01&latitude=100.02",
            content_type="application/json",
        )

        self.assertEqual(response.json()["latitude"], 54.375)
        self.assertEqual(response.json()["longitude"], 24.4375)
        self.assertEqual(response.json()["timezone"], "Coordinated Universal Time")
        self.assertEqual(response.json()["timezone_abbreviation"], "UTC")
        self.assertEqual(response.json()["elevation"], 129.0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("requests.get")
    def test_get_weather_error_response(self, mock_get):
        mock_error_text = "Service not available"
        mock_get.return_value.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_get.return_value.text = mock_error_text

        with self.assertRaises(Exception) as context:
            self.client.get(
                self.api_url + "?longitude=100.01&latitude=100.02",
                content_type="application/json",
            )

        self.assertEqual(
            str(context.exception), "Error fetching weather data: Service not available"
        )
