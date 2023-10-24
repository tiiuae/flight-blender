import json
from api_clients.api_client import ApiClient
from location_vector import LocationVector


class MeteoApiClient(ApiClient):
    def __init__(self):
        self.api_base_url = "https://api.open-meteo.com/v1/forecast" 
        self.available_attrs = ["weathercode", "temperature_2m"]

    def get_data(self, location_vector=None, weather_attrs=["weathercode", "temperature_2m"]):
        self._check_location_vector(location_vector)
        self._check_weather_attrs(weather_attrs)

        return json.dumps({attr: attr for attr in weather_attrs})
    
    def get_api_url(self, location_vector=None):
        self._check_location_vector(location_vector)
        location_vector_query = self._get_location_vector_query_params(location_vector) 
        return "https://api.open-meteo.com/v1/forecast?" + location_vector_query
    
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
            
    def _get_location_vector_query_params(self, location_vector):
        return f"longitude={location_vector.longitude}&latitude={location_vector.latitude}&altitude={location_vector.altitude}"
