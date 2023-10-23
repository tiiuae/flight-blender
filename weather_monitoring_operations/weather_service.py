import requests
from rest_framework import status


class WeatherService:
    def __init__(self, api_url):
        self.api_url = api_url

    def get_weather_data(
        self, longitude, latitude, time, timezone=None, hourly_data=None
    ):
        # Build API request
        params = {
            "longitude": longitude,
            "latitude": latitude,
            "time": time,
            "forecast_days": "1",
        }
        if timezone:
            params["timezone"] = timezone
        if hourly_data:
            params["hourly"] = ",".join(hourly_data)
        url = f"{self.api_url}"
        response = requests.get(url, params=params)

        if response.status_code == status.HTTP_200_OK:
            return response.json()
        else:
            error_message = f"Error fetching weather data: {response.text}"
            raise Exception(error_message)
