
from django.test import TestCase

from api_clients.weather_data.meteo import MeteoApiClient

class MeteoApiClientTestCase(TestCase):
    def test_meteo_api_client(self):
        meteoClient = MeteoApiClient()
        
        self.assertIsInstance(meteoClient, MeteoApiClient)