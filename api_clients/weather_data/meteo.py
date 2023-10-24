import json
from api_clients.api_client import ApiClient
from location_vector import LocationVector


class MeteoApiClient(ApiClient):
    def __init__(self):
        self.available_attrs = ["weathercode", "temperature_2m"]

    def get_data(self, location_vector=None, weather_attrs=["weathercode", "temperature_2m"]):
        self._check_location_vector(location_vector)
        self._check_weather_attrs(weather_attrs)

        return json.dumps({attr: attr for attr in weather_attrs})
    
    def _check_location_vector(self, location_vector):
        if not isinstance(location_vector, LocationVector):
            raise ValueError("Invalid location vector")
        
        for attr in location_vector:
            if not isinstance(attr, (float, int)):
                raise ValueError("Invalid location vector")

    def _check_weather_attrs(self, weather_attrs):
        for attr in weather_attrs:
            if attr not in self.available_attrs:
                raise ValueError(f"Invalid weather attribute: {attr}")
