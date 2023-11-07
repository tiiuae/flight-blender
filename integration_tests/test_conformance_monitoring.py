import json
import threading
import time
from dataclasses import asdict

import arrow
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_helper.common import get_redis
from common.data_definitions import OPERATION_STATES
from conformance_monitoring_operations import models as cfm_models
from conformance_monitoring_operations import tasks as conforming_tasks
from conftest import get_oauth2_token
from flight_declaration_operations import models as fdo_models
from rid_operations import data_definitions as rid_dd

JWT = get_oauth2_token()
REDIS_TELEMETRY_KEY = "all_observations"


class ConformanceMonitoringWithFlights(APITestCase):
    def setUp(self):
        now = arrow.now()
        _one_minute_from_now = now.shift(minutes=1)
        _four_minutes_from_now = now.shift(minutes=4)
        self.r = get_redis()
        self.r.xtrim(REDIS_TELEMETRY_KEY, 0)  # Reset the Telemetry stream
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {JWT}"
        self.flight_declaration_api_url = reverse("set_flight_declaration")
        self.telemetry_set_url = reverse("set_telemetry")
        self.flight_plan = {
            "originating_party": "Medicine Delivery Company",
            "start_datetime": _one_minute_from_now.isoformat(),
            "end_datetime": _four_minutes_from_now.isoformat(),
            "type_of_operation": 1,
            "vehicle_id": "157de9bb-6b49-496b-bf3f-0b768ce6a3b6",
            "submitted_by": "Medicine Company owner",
            "flight_declaration_geo_json": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0",
                            "start_datetime": "",
                            "end_datetime": "",
                            "max_altitude": {"meters": 600.4, "datum": "w84"},
                            "min_altitude": {"meters": 700.4, "datum": "w84"},
                        },
                        "geometry": {
                            "coordinates": [
                                [
                                    [7.470700076878245, 46.988539922914924],
                                    [7.470700076878245, 46.97936054157279],
                                    [7.487045772981162, 46.97936054157279],
                                    [7.487045772981162, 46.988539922914924],
                                    [7.470700076878245, 46.988539922914924],
                                ]
                            ],
                            "type": "Polygon",
                        },
                    }
                ],
            },
        }
        self.rid_json = {
            "reference_time": "2022-07-18T14:22:51.541652+00:00",
            "current_states": [
                {
                    "timestamp": {
                        "value": "2022-07-18T14:22:52.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.9754225199202,
                        "lng": 7.475076017275803,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 181.6975641099569,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:22:53.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97537839156561,
                        "lng": 7.475074106522959,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 187.32256350913605,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:22:54.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97533460388938,
                        "lng": 7.475065885577716,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 192.94755828743686,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:22:55.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97529157858963,
                        "lng": 7.4750514336274,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 198.5725484853129,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:22:56.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97524973002137,
                        "lng": 7.475030889866306,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 204.19753420333566,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:22:57.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.975209461206134,
                        "lng": 7.475004452154652,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 209.8225155857433,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:22:58.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97517115995081,
                        "lng": 7.474972375112586,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 215.44749279959558,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:22:59.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97513519511295,
                        "lng": 7.474934967667648,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 221.07246606410473,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:00.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97510191304869,
                        "lng": 7.47489259007933,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 226.69743567376366,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:01.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.9750716342773,
                        "lng": 7.474845650469361,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 232.32240184321986,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:02.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97504465039461,
                        "lng": 7.474794600891187,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 237.94736498393496,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:03.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97502122126502,
                        "lng": 7.474739932976472,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 243.57232539252175,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:04.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97500157251901,
                        "lng": 7.474682173200564,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 249.19728348406403,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:05.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.974985893380456,
                        "lng": 7.4746218778124875,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 254.82223960689572,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:06.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.974974334844354,
                        "lng": 7.474559627478333,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 260.4471942708127,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:07.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97496700822293,
                        "lng": 7.474496021689548,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 266.0721478626451,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:08.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97496398407367,
                        "lng": 7.474431672990031,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 271.6971007845053,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:09.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97496529151983,
                        "lng": 7.474367201077551,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 277.32205360031514,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:10.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.974970917970175,
                        "lng": 7.474303226836321,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 282.94700666829954,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:11.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97498080924005,
                        "lng": 7.474240366358126,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 288.57196049163485,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:12.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97499487007325,
                        "lng": 7.47417922500962,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 294.19691547654986,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:13.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97501296505933,
                        "lng": 7.474120391602846,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 299.8218720981668,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:14.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.9750349199375,
                        "lng": 7.47406443272514,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 305.44683073280254,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:15.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.975060523274735,
                        "lng": 7.47401188728299,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 311.07179180494865,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:16.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.975089528501826,
                        "lng": 7.473963261312384,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 316.69675569788495,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:17.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.975121656287804,
                        "lng": 7.47391902310561,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 322.32172274232187,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:18.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.9751565972298,
                        "lng": 7.473879598701442,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 327.9466932423215,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:19.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.97519401483258,
                        "lng": 7.4738453677821175,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 333.57166752256273,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:20.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.975233548749024,
                        "lng": 7.473816660016666,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 339.196645789534,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
                {
                    "timestamp": {
                        "value": "2022-07-18T14:23:21.541652+00:00",
                        "format": "RFC3339",
                    },
                    "operational_status": "Airborne",
                    "position": {
                        "lat": 46.975274818250206,
                        "lng": 7.473793751885744,
                        "alt": 620.0,
                        "accuracy_h": "HAUnknown",
                        "accuracy_v": "VAUnknown",
                        "extrapolated": False,
                    },
                    "height": {"distance": 50.0, "reference": "TakeoffLocation"},
                    "track": 344.82162827865955,
                    "speed": 4.91,
                    "timestamp_accuracy": 0.0,
                    "speed_accuracy": "SA3mps",
                    "vertical_speed": 0.0,
                },
            ],
            "flight_details": {
                "rid_details": {
                    "id": "1",
                    "eu_classification": {
                        "category": "EUCategoryUndefined",
                        "class": "EUClassUndefined",
                    },
                    "operator_id": "OP-0xn81lwa",
                    "uas_id": {
                        "serial_number": "f9edf164-1c8f-45d7-9854-bc0ffa33573d",
                        "registration_id": "CHE9t1sq8bqa023t",
                        "utm_id": "07a06bba-5092-48e4-8253-7a523f885bfe",
                    },
                    "operation_description": "Delivery operation, see more details at https://deliveryops.com/operation",
                    "operator_location": {
                        "position": {
                            "lat": 46.97615311620088,
                            "lng": 7.476099729537965,
                        },
                        "altitude": 19.5,
                        "altitude_type": "Takeoff",
                    },
                },
                "aircraft_type": "Helicopter",
            },
        }

    def _set_telemetry(self, flight_declaration_id, rid_json):
        states = rid_json["current_states"]
        rid_flight_details = rid_json["flight_details"]

        eu_classification = rid_flight_details["rid_details"]["eu_classification"]
        uas_id = rid_flight_details["rid_details"]["uas_id"]
        operator_location = rid_flight_details["rid_details"]["operator_location"]

        rid_operator_details = rid_dd.RIDOperatorDetails(
            id=flight_declaration_id,
            uas_id=uas_id,
            operation_description=rid_flight_details["rid_details"][
                "operation_description"
            ],
            operator_id=rid_flight_details["rid_details"]["operator_id"],
            eu_classification=eu_classification,
            operator_location=operator_location,
        )
        rid_auth_data = rid_dd.RIDAuthData(data=0, format="string")

        print("Setting Telemetry"),
        for state in states:
            telemetry_payload = {
                "observations": [
                    {
                        "current_states": [state],
                        "flight_details": {
                            "rid_details": asdict(rid_operator_details),
                            "eu_classification": eu_classification,
                            "uas_id": uas_id,
                            "operator_location": operator_location,
                            "auth_data": asdict(rid_auth_data),
                            "serial_number": "f9edf164-1c8f-45d7-9854-bc0ffa33573d",
                            "aircraft_type": "Helicopter",
                            "operator_name": "Thomas-Roberts",
                            "registration_number": "FA12345897",
                        },
                    }
                ]
            }

            flight_telemetry_response = self.client.put(
                self.telemetry_set_url,
                content_type="application/json",
                data=json.dumps(telemetry_payload),
            )
            self.assertEqual(
                flight_telemetry_response.status_code, status.HTTP_201_CREATED
            )
            print("Sleeping 3 seconds..")
            time.sleep(3)

    # Accepted -> Activated -> (submit telemetry) -> Ended.  !No conformance monitoring is triggered
    # GCS = Ground Control Service.
    def test_f1(self):
        # GCS Submit flight plan and get the accepted state.
        flight_declaration_response = self.client.post(
            self.flight_declaration_api_url,
            content_type="application/json",
            data=json.dumps(self.flight_plan),
        )
        accepted_state = OPERATION_STATES[1][0]
        self.assertEqual(
            flight_declaration_response.json()["message"],
            "Submitted Flight Declaration",
        )
        self.assertEqual(flight_declaration_response.json()["state"], accepted_state)
        self.assertEqual(
            flight_declaration_response.status_code, status.HTTP_201_CREATED
        )

        flight_declaration_id = flight_declaration_response.json()["id"]
        time.sleep(10)  # SLeep 10 seconds

        # GCS Activates the accepted flight request
        activated_state = OPERATION_STATES[2][0]
        activated_state_payload = {
            "state": activated_state,
            "submitted_by": "gcs@handler.com",
        }

        _flight_state_api_url = reverse(
            "flight_declaration_state", kwargs={"pk": flight_declaration_id}
        )
        flight_state_activated_response = self.client.put(
            _flight_state_api_url,
            content_type="application/json",
            data=json.dumps(activated_state_payload),
        )
        self.assertEqual(
            flight_state_activated_response.status_code, status.HTTP_200_OK
        )
        # DB record should have matching states
        fd = fdo_models.FlightDeclaration.objects.get(id=flight_declaration_id)
        self.assertEqual(fd.state, activated_state)

        # Drone submits Telemetry in another thread
        drone_thread = threading.Thread(
            target=self._set_telemetry, args=(flight_declaration_id, self.rid_json)
        )
        drone_thread.start()
        time.sleep(100)
        telemetry_stream_count = self.r.xlen("all_observations")
        self.assertTrue(
            telemetry_stream_count != 0, msg="Telemetry stream length cannot be 0"
        )

        # GCS Ends the activated flight request
        ended_state = OPERATION_STATES[5][0]
        ended_state_payload = {"state": ended_state, "submitted_by": "gcs@handler.com"}

        flight_state_ended_response = self.client.put(
            _flight_state_api_url,
            content_type="application/json",
            data=json.dumps(ended_state_payload),
        )
        self.assertEqual(flight_state_ended_response.status_code, status.HTTP_200_OK)
        # DB record should have matching states
        fd = fdo_models.FlightDeclaration.objects.get(id=flight_declaration_id)
        self.assertEqual(fd.state, ended_state)

    # Accepted -> Activated -> (submit telemetry) -> Contingent -> Ended. !No conformance monitoring is triggered
    # GCS = Ground Control Service.
    def test_f2(self):
        # GCS Submit flight plan and get the accepted state.
        flight_declaration_response = self.client.post(
            self.flight_declaration_api_url,
            content_type="application/json",
            data=json.dumps(self.flight_plan),
        )
        accepted_state = OPERATION_STATES[1][0]
        self.assertEqual(
            flight_declaration_response.json()["message"],
            "Submitted Flight Declaration",
        )
        self.assertEqual(flight_declaration_response.json()["state"], accepted_state)
        self.assertEqual(
            flight_declaration_response.status_code, status.HTTP_201_CREATED
        )

        flight_declaration_id = flight_declaration_response.json()["id"]
        time.sleep(10)  # SLeep 10 seconds

        # GCS Activates the accepted flight request
        activated_state = OPERATION_STATES[2][0]
        activated_state_payload = {
            "state": activated_state,
            "submitted_by": "gcs@handler.com",
        }

        _flight_state_api_url = reverse(
            "flight_declaration_state", kwargs={"pk": flight_declaration_id}
        )
        flight_state_activated_response = self.client.put(
            _flight_state_api_url,
            content_type="application/json",
            data=json.dumps(activated_state_payload),
        )
        self.assertEqual(
            flight_state_activated_response.status_code, status.HTTP_200_OK
        )
        # DB record should have matching states
        fd = fdo_models.FlightDeclaration.objects.get(id=flight_declaration_id)
        self.assertEqual(fd.state, activated_state)

        # Drone submits Telemetry in another thread
        drone_thread = threading.Thread(
            target=self._set_telemetry, args=(flight_declaration_id, self.rid_json)
        )
        drone_thread.start()
        time.sleep(60)
        telemetry_stream_count = self.r.xlen("all_observations")
        self.assertTrue(
            telemetry_stream_count != 0, msg="Telemetry stream length cannot be 0"
        )

        # GCS Sends Contingent to the activated flight request
        contingent_state = OPERATION_STATES[4][0]
        contingent_state_payload = {
            "state": contingent_state,
            "submitted_by": "gcs@handler.com",
        }
        flight_state_contingent_response = self.client.put(
            _flight_state_api_url,
            content_type="application/json",
            data=json.dumps(contingent_state_payload),
        )
        self.assertEqual(
            flight_state_contingent_response.status_code, status.HTTP_200_OK
        )
        # DB record should have matching states
        fd = fdo_models.FlightDeclaration.objects.get(id=flight_declaration_id)
        self.assertEqual(fd.state, contingent_state)

        # GCS Ends the activated flight request
        ended_state = OPERATION_STATES[5][0]
        ended_state_payload = {"state": ended_state, "submitted_by": "gcs@handler.com"}

        flight_state_ended_response = self.client.put(
            _flight_state_api_url,
            content_type="application/json",
            data=json.dumps(ended_state_payload),
        )
        self.assertEqual(flight_state_ended_response.status_code, status.HTTP_200_OK)
        # DB record should have matching states
        fd = fdo_models.FlightDeclaration.objects.get(id=flight_declaration_id)
        self.assertEqual(fd.state, ended_state)

    # Accepted -> Activated -> (submit telemetry)-> Ended Conformance monitoring is enabled
    # GCS = Ground Control Service.
    def test_f3(self):
        # GCS Submit flight plan and get the accepted state.
        flight_declaration_response = self.client.post(
            self.flight_declaration_api_url,
            content_type="application/json",
            data=json.dumps(self.flight_plan),
        )
        accepted_state = OPERATION_STATES[1][0]
        self.assertEqual(
            flight_declaration_response.json()["message"],
            "Submitted Flight Declaration",
        )
        self.assertEqual(flight_declaration_response.json()["state"], accepted_state)
        self.assertEqual(
            flight_declaration_response.status_code, status.HTTP_201_CREATED
        )

        flight_declaration_id = flight_declaration_response.json()["id"]
        time.sleep(10)  # Sleep 10 seconds

        # GCS Activates the accepted flight request
        activated_state = OPERATION_STATES[2][0]
        activated_state_payload = {
            "state": activated_state,
            "submitted_by": "gcs@handler.com",
        }

        _flight_state_api_url = reverse(
            "flight_declaration_state", kwargs={"pk": flight_declaration_id}
        )
        flight_state_activated_response = self.client.put(
            _flight_state_api_url,
            content_type="application/json",
            data=json.dumps(activated_state_payload),
        )
        self.assertEqual(
            flight_state_activated_response.status_code, status.HTTP_200_OK
        )
        # Flight state in DB is in accepted state
        fd = fdo_models.FlightDeclaration.objects.get(id=flight_declaration_id)
        self.assertEqual(fd.state, activated_state)
        # Flight authorization DB record is created
        fa = fdo_models.FlightAuthorization.objects.filter(declaration=fd).first()
        self.assertIsNotNone(fa)

        # The scheduler task for the accepted->activated state flight should be created in DB
        task = cfm_models.TaskScheduler.objects.get(
            flight_declaration_id=flight_declaration_id
        )
        self.assertIsNotNone(task)

        # Drone submits Telemetry in another thread
        drone_thread = threading.Thread(
            target=self._set_telemetry, args=(flight_declaration_id, self.rid_json)
        )
        drone_thread.start()
        time.sleep(30)

        telemetry_stream_count = self.r.xlen("all_observations")
        self.assertTrue(
            telemetry_stream_count != 0, msg="Telemetry stream length cannot be 0"
        )
        # IMPORTANT: Celery task : check_flight_conformance() will not trigger automatically in the test framework. Hence triggering it manually.
        # Mock Latest Telemetry DateTime since the TaskScheduler is not running in unit test
        fd.latest_telemetry_datetime = arrow.now().isoformat()
        fd.save()
        conforming_tasks.check_flight_conformance(
            flight_declaration_id=flight_declaration_id
        )

        # GCS Ends the activated flight request
        ended_state = OPERATION_STATES[5][0]
        ended_state_payload = {"state": ended_state, "submitted_by": "gcs@handler.com"}

        flight_state_ended_response = self.client.put(
            _flight_state_api_url,
            content_type="application/json",
            data=json.dumps(ended_state_payload),
        )
        self.assertEqual(flight_state_ended_response.status_code, status.HTTP_200_OK)
        # DB record should have matching states

        fd = fdo_models.FlightDeclaration.objects.get(id=flight_declaration_id)
        self.assertEqual(fd.state, ended_state)

        # Corresponding flight track records should also be created in the DB
        flight_trackings = fdo_models.FlightOperationTracking.objects.filter(
            flight_declaration_id=flight_declaration_id
        )

        self.assertEqual(len(flight_trackings), 3)
        self.assertEqual(flight_trackings[0].notes, "Created Declaration")
        self.assertEqual(flight_trackings[1].notes, "State changed by operator")
        self.assertEqual(flight_trackings[2].notes, "State changed by operator")


    # Accepted -> Activated -> Conformance monitoring is enabled
    # GCS = Ground Control Service.
    def test_f4_no_telemetry(self):
        # GCS Submit flight plan and get the accepted state.
        flight_declaration_response = self.client.post(
            self.flight_declaration_api_url,
            content_type="application/json",
            data=json.dumps(self.flight_plan),
        )
        accepted_state = OPERATION_STATES[1][0]
        self.assertEqual(
            flight_declaration_response.json()["message"],
            "Submitted Flight Declaration",
        )
        self.assertEqual(flight_declaration_response.json()["state"], accepted_state)
        self.assertEqual(
            flight_declaration_response.status_code, status.HTTP_201_CREATED
        )

        flight_declaration_id = flight_declaration_response.json()["id"]
        time.sleep(10)  # Sleep 10 seconds

        # GCS Activates the accepted flight request
        activated_state = OPERATION_STATES[2][0]
        activated_state_payload = {
            "state": activated_state,
            "submitted_by": "gcs@handler.com",
        }

        _flight_state_api_url = reverse(
            "flight_declaration_state", kwargs={"pk": flight_declaration_id}
        )
        flight_state_activated_response = self.client.put(
            _flight_state_api_url,
            content_type="application/json",
            data=json.dumps(activated_state_payload),
        )
        self.assertEqual(
            flight_state_activated_response.status_code, status.HTTP_200_OK
        )
        # Flight state in DB is in accepted state
        fd = fdo_models.FlightDeclaration.objects.get(id=flight_declaration_id)
        self.assertEqual(fd.state, activated_state)
        # Flight authorization DB record is created
        fa = fdo_models.FlightAuthorization.objects.filter(declaration=fd).first()
        self.assertIsNotNone(fa)

        # The scheduler task for the accepted->activated state flight should be created in DB
        task = cfm_models.TaskScheduler.objects.get(
            flight_declaration_id=flight_declaration_id
        )
        self.assertIsNotNone(task)

        time.sleep(15)

        telemetry_stream_count = self.r.xlen("all_observations")
        self.assertTrue(
            telemetry_stream_count == 0, msg="Telemetry stream length should be 0"
        )
        # IMPORTANT: Celery task : check_flight_conformance() will not trigger automatically in the test framework. Hence triggering it manually.
        # Mock Latest Telemetry DateTime since the TaskScheduler is not running in unit test
        fd.latest_telemetry_datetime = arrow.now().isoformat()
        fd.save()
        conforming_tasks.check_flight_conformance(
            flight_declaration_id=flight_declaration_id
        )


        # Corresponding flight track records should also be created in the DB
        flight_trackings = fdo_models.FlightOperationTracking.objects.filter(
            flight_declaration_id=flight_declaration_id
        )
        print("Tracking...")
        for x in flight_trackings:
            print(x.notes)

        # self.assertEqual(len(flight_trackings), 3)
        # self.assertEqual(flight_trackings[0].notes, "Created Declaration")
        # self.assertEqual(flight_trackings[1].notes, "State changed by operator")
        # self.assertEqual(flight_trackings[2].notes, "State changed by operator")
