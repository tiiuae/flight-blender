import json
from django.test import TestCase

from api_clients.weather_data.meteo import MeteoApiClient


class MeteoApiClientTestCase(TestCase):
    def setUp(self):
        self.client = MeteoApiClient()

    def test_meteo_api_client(self):
        
        self.assertIsInstance(self.client, MeteoApiClient)
        
        data = self.client.get_data()
        
        self.assertIsNotNone(data)
        
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            self.fail("Data is not valid JSON")

        self.assertIsInstance(parsed_data, dict)