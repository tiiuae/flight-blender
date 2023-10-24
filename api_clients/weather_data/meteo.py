import json
from api_clients.api_client import ApiClient



class MeteoApiClient(ApiClient):
    def __init__(self):
        self.available_attrs = ["weathercode", "temperature_2m"]

    def get_data(self,weather_attrs=["weathercode", "temperature_2m"]):
        
        self.check_weather_attrs(weather_attrs)          

        return json.dumps({attr: attr for attr in weather_attrs})        
                 
    def check_weather_attrs(self, weather_attrs):
        for attr in weather_attrs:
            if attr not in self.available_attrs:
                raise ValueError(f"Invalid weather attribute: {attr}")