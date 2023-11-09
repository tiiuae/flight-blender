import json
from os import environ as env

import arrow
import pytest
import requests
from rest_framework import status

from flight_declaration_operations import models as fdo_models
from non_repudiation import models as nr_models


def get_oauth2_token():
    # Request a new OAuth2 token
    data = {
        "grant_type": "client_credentials",
        "client_id": env.get("CLIENT_ID", ""),
        "client_secret": env.get("CLIENT_SECRET", ""),
        "scope": "blender.write blender.read",
        "audience": env.get("PASSPORT_AUDIENCE", ""),
    }
    token_url = env.get("PASSPORT_URL", "") + env.get("PASSPORT_TOKEN_URL", "")
    response = requests.post(token_url, data=data)

    # Check for a successful response and return the token
    if response.status_code == status.HTTP_200_OK:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        raise ValueError(
            f"Failed to obtain OAuth2 token. Status code: {response.status_code}"
        )


@pytest.fixture(scope="function")
def mock_env_passport_url():
    # Set the environment variable PASSPORT_URL to the mocked value
    original_passport_url = env.get("PASSPORT_URL", "")
    env["PASSPORT_URL"] = "https://invalid_passporturl.com"

    # Yield control back to the test
    yield

    # Restore the environment variable: PASSPORT_URL to its original value
    env["PASSPORT_URL"] = original_passport_url


@pytest.fixture(scope="function")
def mock_env_secret_key():
    # Set the environment variable SECRET_KEY to the mocked value
    original_secret_key = env.get("SECRET_KEY", "")

    with open("security/test_keys/001.key", "r") as key_file:
        private_key = key_file.read()
    env["SECRET_KEY"] = private_key

    # Yield control back to the test
    yield

    # Restore the environment variable: PASSPORT_URL to its original value
    env["SECRET_KEY"] = original_secret_key


@pytest.mark.django_db
@pytest.fixture(scope="function")
def create_flight_plans(db) -> None:
    # Flight plan 1
    max_alt = 100
    min_alt = 90
    flight_s_time = "2023-08-01T9:00:00+00:00"
    flight_e_time = "2023-08-01T10:00:00+00:00"
    fdo_models.FlightDeclaration.objects.create(
        operational_intent={
            "volumes": [
                {
                    "volume": {
                        "outline_polygon": {
                            "vertices": [
                                {
                                    "lat": 3.0000070710678117,
                                    "lng": 1.999992928932188,
                                },
                                {
                                    "lat": 3.000007730104534,
                                    "lng": 1.9999936560671583,
                                },
                                {
                                    "lat": 2.0000070710678117,
                                    "lng": 0.9999929289321882,
                                },
                            ]
                        },
                        "altitude_lower": {
                            "value": min_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "altitude_upper": {
                            "value": max_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "outline_circle": None,
                    },
                    "time_start": {
                        "format": "RFC3339",
                        "value": "2023-07-26T15:00:00+00:00",
                    },
                    "time_end": {
                        "format": "RFC3339",
                        "value": "2023-07-26T16:00:00+00:00",
                    },
                }
            ],
            "priority": 0,
            "state": "Accepted",
            "off_nominal_volumes": [],
        },
        bounds="",
        type_of_operation=1,
        aircraft_id="112233",
        submitted_by="User 001",
        is_approved=False,
        state=1,
        start_datetime=flight_s_time,
        end_datetime=flight_e_time,
        originating_party="Party 001",
        flight_declaration_raw_geojson=json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-08-10T16:29:08.842Z",
                            "end_datetime": "2023-08-10T19:29:08.842Z",
                            "max_altitude": {"meters": max_alt, "datum": "agl"},
                            "min_altitude": {"meters": min_alt, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [[1, 2], [2, 3]],
                            "type": "LineString",
                        },
                    }
                ],
            }
        ),
    )
    # Flight plan 2

    max_alt = 120
    min_alt = 70
    flight_s_time = "2023-08-01T11:00:00+00:00"
    flight_e_time = "2023-08-01T12:00:00+00:00"
    fdo_models.FlightDeclaration.objects.create(
        operational_intent={
            "volumes": [
                {
                    "volume": {
                        "outline_polygon": {
                            "vertices": [
                                {
                                    "lat": 3.0000070710678117,
                                    "lng": 1.999992928932188,
                                },
                                {
                                    "lat": 3.000007730104534,
                                    "lng": 1.9999936560671583,
                                },
                                {
                                    "lat": 2.0000070710678117,
                                    "lng": 0.9999929289321882,
                                },
                            ]
                        },
                        "altitude_lower": {
                            "value": min_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "altitude_upper": {
                            "value": max_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "outline_circle": None,
                    },
                    "time_start": {
                        "format": "RFC3339",
                        "value": "2023-07-26T15:00:00+00:00",
                    },
                    "time_end": {
                        "format": "RFC3339",
                        "value": "2023-07-26T16:00:00+00:00",
                    },
                }
            ],
            "priority": 0,
            "state": "Accepted",
            "off_nominal_volumes": [],
        },
        bounds="",
        type_of_operation=1,
        submitted_by="User 002",
        is_approved=False,
        state=2,
        start_datetime=flight_s_time,
        end_datetime=flight_e_time,
        originating_party="Party 002",
        flight_declaration_raw_geojson=json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-08-10T16:29:08.842Z",
                            "end_datetime": "2023-08-10T19:29:08.842Z",
                            "max_altitude": {"meters": max_alt, "datum": "agl"},
                            "min_altitude": {"meters": min_alt, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [[1, 2], [2, 3]],
                            "type": "LineString",
                        },
                    }
                ],
            }
        ),
    )
    # Flight plan 3
    max_alt = 100
    min_alt = 80
    flight_s_time = "2023-08-01T15:00:00+00:00"
    flight_e_time = "2023-08-01T16:00:00+00:00"
    fdo_models.FlightDeclaration.objects.create(
        operational_intent={
            "volumes": [
                {
                    "volume": {
                        "outline_polygon": {
                            "vertices": [
                                {
                                    "lat": 3.0000070710678117,
                                    "lng": 1.999992928932188,
                                },
                                {
                                    "lat": 3.000007730104534,
                                    "lng": 1.9999936560671583,
                                },
                                {
                                    "lat": 2.0000070710678117,
                                    "lng": 0.9999929289321882,
                                },
                            ]
                        },
                        "altitude_lower": {
                            "value": min_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "altitude_upper": {
                            "value": max_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "outline_circle": None,
                    },
                    "time_start": {
                        "format": "RFC3339",
                        "value": "2023-07-26T15:00:00+00:00",
                    },
                    "time_end": {
                        "format": "RFC3339",
                        "value": "2023-07-26T16:00:00+00:00",
                    },
                }
            ],
            "priority": 0,
            "state": "Accepted",
            "off_nominal_volumes": [],
        },
        bounds="",
        type_of_operation=1,
        aircraft_id="334455",
        submitted_by="User 003",
        is_approved=False,
        state=3,
        start_datetime=flight_s_time,
        end_datetime=flight_e_time,
        originating_party="Party 003",
        flight_declaration_raw_geojson=json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-08-10T16:29:08.842Z",
                            "end_datetime": "2023-08-10T19:29:08.842Z",
                            "max_altitude": {"meters": max_alt, "datum": "agl"},
                            "min_altitude": {"meters": min_alt, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [[1, 2], [2, 3]],
                            "type": "LineString",
                        },
                    }
                ],
            }
        ),
    )
    yield
    fdo_models.FlightDeclaration.objects.all().delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def submit_flight_plan_for_conformance_monitoring_no_auth(db) -> None:
    max_alt = 100
    min_alt = 90
    flight_s_time = "2023-08-01T9:00:00+00:00"
    flight_e_time = "2023-08-01T10:00:00+00:00"
    fdo_models.FlightDeclaration.objects.create(
        operational_intent={
            "volumes": [
                {
                    "volume": {
                        "outline_polygon": {
                            "vertices": [
                                {
                                    "lat": 3.0000070710678117,
                                    "lng": 1.999992928932188,
                                },
                                {
                                    "lat": 3.000007730104534,
                                    "lng": 1.9999936560671583,
                                },
                                {
                                    "lat": 2.0000070710678117,
                                    "lng": 0.9999929289321882,
                                },
                            ]
                        },
                        "altitude_lower": {
                            "value": min_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "altitude_upper": {
                            "value": max_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "outline_circle": None,
                    },
                    "time_start": {
                        "format": "RFC3339",
                        "value": "2023-07-26T15:00:00+00:00",
                    },
                    "time_end": {
                        "format": "RFC3339",
                        "value": "2023-07-26T16:00:00+00:00",
                    },
                }
            ],
            "priority": 0,
            "state": "Accepted",
            "off_nominal_volumes": [],
        },
        bounds="",
        type_of_operation=1,
        aircraft_id="990099",
        submitted_by="GCS handler 001",
        is_approved=False,
        state=1,
        start_datetime=flight_s_time,
        end_datetime=flight_e_time,
        originating_party="Guide mission 001",
        flight_declaration_raw_geojson=json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-08-10T16:29:08.842Z",
                            "end_datetime": "2023-08-10T19:29:08.842Z",
                            "max_altitude": {"meters": max_alt, "datum": "agl"},
                            "min_altitude": {"meters": min_alt, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [[1, 2], [2, 3]],
                            "type": "LineString",
                        },
                    }
                ],
            }
        ),
    )
    yield
    fdo_models.FlightDeclaration.objects.all().delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def submit_flight_plan_for_conformance_monitoring_with_auth(db) -> None:
    max_alt = 100
    min_alt = 90
    flight_s_time = "2023-08-01T9:00:00+00:00"
    flight_e_time = "2023-08-01T10:00:00+00:00"
    fd = fdo_models.FlightDeclaration.objects.create(
        operational_intent={
            "volumes": [
                {
                    "volume": {
                        "outline_polygon": {
                            "vertices": [
                                {
                                    "lat": 3.0000070710678117,
                                    "lng": 1.999992928932188,
                                },
                                {
                                    "lat": 3.000007730104534,
                                    "lng": 1.9999936560671583,
                                },
                                {
                                    "lat": 2.0000070710678117,
                                    "lng": 0.9999929289321882,
                                },
                            ]
                        },
                        "altitude_lower": {
                            "value": min_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "altitude_upper": {
                            "value": max_alt,
                            "reference": "W84",
                            "units": "M",
                        },
                        "outline_circle": None,
                    },
                    "time_start": {
                        "format": "RFC3339",
                        "value": "2023-07-26T15:00:00+00:00",
                    },
                    "time_end": {
                        "format": "RFC3339",
                        "value": "2023-07-26T16:00:00+00:00",
                    },
                }
            ],
            "priority": 0,
            "state": "Accepted",
            "off_nominal_volumes": [],
        },
        bounds="",
        type_of_operation=1,
        aircraft_id="990099",
        submitted_by="GCS handler 001",
        is_approved=False,
        state=1,
        start_datetime=flight_s_time,
        end_datetime=flight_e_time,
        originating_party="Guide mission 001",
        flight_declaration_raw_geojson=json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-08-10T16:29:08.842Z",
                            "end_datetime": "2023-08-10T19:29:08.842Z",
                            "max_altitude": {"meters": max_alt, "datum": "agl"},
                            "min_altitude": {"meters": min_alt, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [[1, 2], [2, 3]],
                            "type": "LineString",
                        },
                    }
                ],
            }
        ),
    )

    fdo_models.FlightAuthorization.objects.create(declaration=fd)
    yield
    fdo_models.FlightDeclaration.objects.all().delete()
    fdo_models.FlightAuthorization.objects.all().delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def submit_real_time_flight_plan_for_conformance_monitoring_with_auth(db) -> None:
    max_alt = 100
    min_alt = 90
    now = arrow.now()
    flight_s_time = now.shift(seconds=-5).isoformat()
    flight_e_time = now.shift(seconds=60).isoformat()
    fd = fdo_models.FlightDeclaration.objects.create(
        operational_intent={
            "state": "Accepted",
            "volumes": [
                {
                    "volume": {
                        "altitude_lower": {
                            "units": "M",
                            "value": min_alt,
                            "reference": "W84",
                        },
                        "altitude_upper": {
                            "units": "M",
                            "value": max_alt,
                            "reference": "W84",
                        },
                        "outline_circle": None,
                        "outline_polygon": {
                            "vertices": [
                                {"lat": 46.98854992291493, "lng": 7.470700076878245},
                                {"lat": 46.98854992291493, "lng": 7.487045772981162},
                                {"lat": 46.98854987476219, "lng": 7.4870467531525655},
                                {"lat": 46.98854973076773, "lng": 7.487047723884382},
                                {"lat": 46.988549492318285, "lng": 7.487048675827935},
                                {"lat": 46.988549161710246, "lng": 7.487049599815486},
                                {"lat": 46.98854874212757, "lng": 7.48705048694853},
                                {"lat": 46.98854823761105, "lng": 7.487051328683492},
                                {"lat": 46.98854765301946, "lng": 7.487052116914003},
                                {"lat": 46.98854699398274, "lng": 7.487052844048974},
                                {"lat": 46.98854626684776, "lng": 7.487053503085695},
                                {"lat": 46.988545478617255, "lng": 7.487054087677285},
                                {"lat": 46.988544636882295, "lng": 7.487054592193806},
                                {"lat": 46.98854374974925, "lng": 7.487055011776487},
                                {"lat": 46.9885428257617, "lng": 7.48705534238452},
                                {"lat": 46.98854187381814, "lng": 7.487055580833966},
                                {"lat": 46.988540903086324, "lng": 7.487055724828429},
                                {"lat": 46.988539922914924, "lng": 7.4870557729811615},
                                {"lat": 46.97936054157279, "lng": 7.4870557729811615},
                                {"lat": 46.97935956140139, "lng": 7.487055724828429},
                                {"lat": 46.97935859066957, "lng": 7.487055580833966},
                                {"lat": 46.979357638726015, "lng": 7.48705534238452},
                                {"lat": 46.979356714738465, "lng": 7.487055011776487},
                                {"lat": 46.97935582760542, "lng": 7.487054592193806},
                                {"lat": 46.97935498587046, "lng": 7.487054087677285},
                                {"lat": 46.97935419763995, "lng": 7.487053503085695},
                                {"lat": 46.979353470504975, "lng": 7.487052844048974},
                                {"lat": 46.97935281146825, "lng": 7.487052116914003},
                                {"lat": 46.979352226876664, "lng": 7.487051328683492},
                                {"lat": 46.97935172236014, "lng": 7.48705048694853},
                                {"lat": 46.97935130277747, "lng": 7.487049599815486},
                                {"lat": 46.97935097216943, "lng": 7.487048675827935},
                                {"lat": 46.97935073371998, "lng": 7.487047723884382},
                                {"lat": 46.97935058972552, "lng": 7.4870467531525655},
                                {"lat": 46.979350541572785, "lng": 7.487045772981162},
                                {"lat": 46.979350541572785, "lng": 7.470700076878245},
                                {"lat": 46.97935058972552, "lng": 7.470699096706841},
                                {"lat": 46.97935073371998, "lng": 7.470698125975025},
                                {"lat": 46.97935097216943, "lng": 7.470697174031472},
                                {"lat": 46.97935130277747, "lng": 7.470696250043921},
                                {"lat": 46.97935172236014, "lng": 7.4706953629108765},
                                {"lat": 46.979352226876664, "lng": 7.470694521175915},
                                {"lat": 46.97935281146825, "lng": 7.470693732945404},
                                {"lat": 46.979353470504975, "lng": 7.470693005810433},
                                {"lat": 46.97935419763995, "lng": 7.470692346773712},
                                {"lat": 46.97935498587046, "lng": 7.470691762182122},
                                {"lat": 46.97935582760542, "lng": 7.470691257665601},
                                {"lat": 46.979356714738465, "lng": 7.47069083808292},
                                {"lat": 46.979357638726015, "lng": 7.470690507474887},
                                {"lat": 46.97935859066957, "lng": 7.470690269025441},
                                {"lat": 46.97935956140139, "lng": 7.470690125030978},
                                {"lat": 46.97936054157279, "lng": 7.470690076878245},
                                {"lat": 46.988539922914924, "lng": 7.470690076878245},
                                {"lat": 46.988540903086324, "lng": 7.470690125030978},
                                {"lat": 46.98854187381814, "lng": 7.470690269025441},
                                {"lat": 46.9885428257617, "lng": 7.470690507474887},
                                {"lat": 46.98854374974925, "lng": 7.47069083808292},
                                {"lat": 46.988544636882295, "lng": 7.470691257665601},
                                {"lat": 46.988545478617255, "lng": 7.470691762182122},
                                {"lat": 46.98854626684776, "lng": 7.470692346773712},
                                {"lat": 46.98854699398274, "lng": 7.470693005810433},
                                {"lat": 46.98854765301946, "lng": 7.470693732945404},
                                {"lat": 46.98854823761105, "lng": 7.470694521175915},
                                {"lat": 46.98854874212757, "lng": 7.4706953629108765},
                                {"lat": 46.988549161710246, "lng": 7.470696250043921},
                                {"lat": 46.988549492318285, "lng": 7.470697174031472},
                                {"lat": 46.98854973076773, "lng": 7.470698125975025},
                                {"lat": 46.98854987476219, "lng": 7.470699096706841},
                            ]
                        },
                    },
                    "time_end": {
                        "value": "2023-11-09T10:48:32.991852+00:00",
                        "format": "RFC3339",
                    },
                    "time_start": {
                        "value": "2023-11-09T10:45:32.991852+00:00",
                        "format": "RFC3339",
                    },
                }
            ],
            "priority": 0,
            "off_nominal_volumes": [],
        },
        bounds="",
        type_of_operation=1,
        aircraft_id="990099",
        submitted_by="GCS handler 001",
        is_approved=False,
        state=1,
        start_datetime=flight_s_time,
        end_datetime=flight_e_time,
        originating_party="Guide mission 001",
        flight_declaration_raw_geojson=json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "2023-08-10T16:29:08.842Z",
                            "end_datetime": "2023-08-10T19:29:08.842Z",
                            "max_altitude": {"meters": max_alt, "datum": "agl"},
                            "min_altitude": {"meters": min_alt, "datum": "agl"},
                        },
                        "geometry": {
                            "coordinates": [[1, 2], [2, 3]],
                            "type": "LineString",
                        },
                    }
                ],
            }
        ),
    )

    fdo_models.FlightAuthorization.objects.create(declaration=fd)
    yield
    fdo_models.FlightDeclaration.objects.all().delete()
    fdo_models.FlightAuthorization.objects.all().delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def create_public_keys(db) -> None:
    nr_models.PublicKey.objects.create(
        key_id="001", url="http://publickeyTrue.com", is_active=True
    )

    nr_models.PublicKey.objects.create(
        key_id="002", url="http://publickeyFalse.com", is_active=False
    )

    nr_models.PublicKey.objects.create(
        key_id="003", url="http://publickey.com", is_active=True
    )
    yield
    nr_models.PublicKey.objects.all().delete()
