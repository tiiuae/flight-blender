from rest_framework.test import APITestCase

from django.urls import reverse
from conftest import get_oauth2_token
from unittest.mock import patch
from .views import _fetch_weather_data

JWT = get_oauth2_token()


# Create your tests here.
class WeatherMonitoringOperationsTestCase(APITestCase):
    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
        self.api_url = reverse("get_weather_data")

    def test_get_weather(self):
        response = self.client.get(self.api_url, content_type="application/json")

        print(response.content)

        assert response.status_code == 200

        assert response["Content-Type"] == "application/json"

    @patch("requests.get")
    def test_fetch_weather_data(self, mock_get):
        mock_response = {
            "weather": "sunny",
            "temperature": "70",
            "wind_speed": "10",
            "wind_direction": "N",
            "precipitation": "0",
            "visibility": "10",
            "cloud_coverage": "0",
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        data = _fetch_weather_data()

        assert data == mock_response
