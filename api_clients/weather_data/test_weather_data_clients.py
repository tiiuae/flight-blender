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
        
        parsed_data = self._parse_data_fail_on_exception(data)
        self.assertIsInstance(parsed_data, dict)
        
    def test_meteo_api_client_with_query_params(self):
        self.client = MeteoApiClient()    
        
        self.assertIsInstance(self.client, MeteoApiClient)
        
        data = self.client.get_data(["weathercode", "temperature_2m"])
        parsed_data = self._parse_data_fail_on_exception(data)
        
        self.assertIsNotNone(parsed_data.get("weathercode"))
        self.assertIsNotNone(parsed_data.get("temperature_2m"))
        self.assertIsNone(parsed_data.get("random"))
            
    def _parse_data_fail_on_exception(self, data):
        try:
            return json.loads(data)
        except:
            self.fail("Data is not valid JSON")
    