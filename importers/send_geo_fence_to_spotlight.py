## A file to import flight data into the Secured Flight Spotlight instance.
import json
from datetime import datetime, timedelta
from os import environ as env

import geojson
import requests
from auth_factory import (
    NoAuthCredentialsGetter,
    PassportCredentialsGetter,
    PassportSpotlightCredentialsGetter,
)
from dotenv import find_dotenv, load_dotenv
from geojson import Polygon

from common import get_redis

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


class PassportCredentialsGetter:
    def __init__(self):
        pass

    def get_cached_credentials(self):
        r = get_redis()

        now = datetime.now()

        token_details = r.get("access_token_details")
        if token_details:
            token_details = json.loads(token_details)
            created_at = token_details["created_at"]
            set_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_write_credentials()
                r.set(
                    "access_token_details",
                    json.dumps(
                        {"credentials": credentials, "created_at": now.isoformat()}
                    ),
                )
            else:
                credentials = token_details["credentials"]
        else:
            credentials = self.get_write_credentials()
            r.set(
                "access_token_details",
                json.dumps({"credentials": credentials, "created_at": now.isoformat()}),
            )

            r.expire("access_token_details", timedelta(minutes=58))

        return credentials

    def get_write_credentials(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": env.get("SPOTLIGHT_WRITE_CLIENT_ID"),
            "client_secret": env.get("SPOTLIGHT_WRITE_CLIENT_SECRET"),
            "audience": env.get("SPOTLIGHT_AUDIENCE"),
            "scope": env.get("SPOTLIGHT_GEO_FENCE_SCOPE"),
        }
        url = env.get("PASSPORT_URL") + env.get("PASSPORT_TOKEN_URL")

        token_data = requests.post(url, data=payload)
        t_data = token_data.json()
        return t_data


class FlightSpotlightUploader:
    def __init__(self, credentials):
        self.credentials = credentials

    def upload_to_server(self, filename):
        with open(filename, "r") as geo_fence_json_file:
            geo_fence_json = geo_fence_json_file.read()

        geo_fence_data = json.loads(geo_fence_json)

        for fence_feature in geo_fence_data["features"]:
            headers = {"Authorization": "Bearer " + self.credentials["access_token"]}

            upper_limit = fence_feature["properties"]["upper_limit"]
            lower_limit = fence_feature["properties"]["lower_limit"]

            try:
                p = Polygon(fence_feature["geometry"]["coordinates"])
                assert p.is_valid
            except AssertionError as ae:
                print("Invalid polygon in Geofence")
            else:
                payload = {
                    "geo_fence": geojson.dumps(p, sort_keys=True),
                    "properties": json.dumps(
                        {"upper_limit": upper_limit, "lower_limit": lower_limit}
                    ),
                }
                securl = env.get("FLIGHT_SPOTLIGHT_URL") + "/set_geo_fence"
                try:
                    response = requests.post(securl, data=payload, headers=headers)
                    print(response.content)
                except Exception as e:
                    print(e)
                else:
                    print("Uploaded Geo Fence")


if __name__ == "__main__":
    # my_credentials = PassportSpotlightCredentialsGetter()
    my_credentials = NoAuthCredentialsGetter()
    credentials = my_credentials.get_cached_credentials(
        audience="testflight.flightspotlight.com", scopes=["spotlight.write"]
    )

    my_uploader = FlightSpotlightUploader(credentials=credentials)
    my_uploader.upload_to_server(filename="aoi_geo_fence_samples/geo_fence.geojson")
