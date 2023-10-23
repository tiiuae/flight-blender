import json
from api_clients.api_client import ApiClient


class MeteoApiClient(ApiClient):
    def __init__(self, weather_attrs=None):
        self.weather_attrs = weather_attrs

    def get_data(self):  
        return json.dumps({
            "foo": "bar"
        })
