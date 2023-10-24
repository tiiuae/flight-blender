import json
from django.test import TestCase

from urllib.parse import urlparse, parse_qs

from api_clients.weather_data.meteo import MeteoApiClient
from location_vector import LocationVector


class MeteoApiClientTestCase(TestCase):
    def setUp(self):
        self.client = MeteoApiClient()
        self.valid_location_vector = LocationVector(24.4512, 54.397, 2)

        self.assertTupleEqual(self.valid_location_vector, (24.4512, 54.397, 2))
        self.assertIsNotNone(self._parse_data_fail_on_exception('{"test": "test"}'))
        self.assertRaises(Exception, self._parse_data_fail_on_exception, "random")

    def test_meteo_api_client_with_missing_location_vector(self):
        location_vector = None
        self.assertIsInstance(self.client, MeteoApiClient)
        self.assertRaises(ValueError, self.client.get_data, location_vector)

    def test_meteo_api_client_with_invalid_location_vector(self):
        invalid_location_vector = LocationVector(24.4512, 54.397, "w")
        self.assertRaises(ValueError, self.client.get_data, invalid_location_vector)

    def test_meteo_api_client_with_location_vector(self):
        data = self.client.get_data(
            self.valid_location_vector, ["weathercode", "temperature_2m"]
        )
        parsed_data = self._parse_data_fail_on_exception(data)

        self.assertIsNotNone(parsed_data.get("weathercode"))
        self.assertIsNotNone(parsed_data.get("temperature_2m"))

    def test_meteo_api_client_get_data(self):
        data = self.client.get_data(self.valid_location_vector)
        self.assertIsNotNone(data)

        parsed_data = self._parse_data_fail_on_exception(data)
        self.assertIsInstance(parsed_data, dict)

    def test_meteo_api_client_get_data_with_query_params(self):
        self.assertIsInstance(self.client, MeteoApiClient)

        data = self.client.get_data(
            self.valid_location_vector, ["weathercode", "temperature_2m"]
        )
        parsed_data = self._parse_data_fail_on_exception(data)

        self.assertIsNotNone(parsed_data.get("weathercode"))
        self.assertIsNotNone(parsed_data.get("temperature_2m"))
        self.assertIsNone(parsed_data.get("random"))
        self.assertRaises(ValueError, self.client.get_data, ["random"])

    def test_meteo_api_client_get_api_url_with_location_vector(self):
        self.assertRaises(
            ValueError,
            self.client.get_api_url,
            location_vector=self.valid_location_vector,
        )

        url = self.client.get_api_url(
            location_vector=self.valid_location_vector,
            weather_attrs=["weathercode", "temperature_2m"],
        )

        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        self.assertEqual(query_params, query_params | {"latitude": ["24.4512"]})
        self.assertEqual(query_params, query_params | {"longitude": ["54.397"]})
        self.assertEqual(query_params, query_params | {"elevation": ["2"]})

        self.assertEqual("hourly=weathercode,temperature_2m" in url, True)

    def _parse_data_fail_on_exception(self, data):
        try:
            return json.loads(data)
        except:
            self.fail("Data is not valid JSON")
