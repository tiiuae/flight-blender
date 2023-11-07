## This file checks the conformance of a operation per the AMC stated in the EU Conformance monitoring service
import json
import logging
from typing import List

import arrow
from dotenv import find_dotenv, load_dotenv
from shapely.geometry import Point
from shapely.geometry import Polygon as Plgn

from conformance_monitoring_operations.data_definitions import PolygonAltitude
from scd_operations.data_definitions import LatLngPoint, Polygon, Volume4D

from .conformance_state_checks import ConformanceChecksList
from .data_helper import cast_to_volume4d
from conformance_monitoring_operations import db_operations as db_ops
from flight_declaration_operations import models as fdo_models
from common.data_definitions import OPERATION_STATES

load_dotenv(find_dotenv())


def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    # Source: https://stackoverflow.com/questions/10048249/how-do-i-determine-if-current-time-is-within-a-specified-range-using-pythons-da
    check_time = check_time or arrow.now()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else:  # crosses midnight
        return check_time >= begin_time or check_time <= end_time


class BlenderConformanceEngine:
    def is_operation_conformant_via_telemetry(
        self,
        flight_declaration_id: str,
        aircraft_id: str,
        telemetry_location: LatLngPoint,
        altitude_m_wgs_84: float,
    ) -> bool:
        """This method performs the conformance sequence per AMC1 Article 13(1) as specified in the EU AMC / GM on U-Space regulation.
        This method is called every time a telemetry has been sent into Flight Blender. Specifically, it checks this once a telemetry has been sent:
         - C2 Check if flight authorization is granted
         - C3 Match telemetry from aircraft with the flight authorization
         - C4 Determine whether the aircraft is subject to an accepted and activated flight authorization
         - C5 Check if flight operation is activated
         - C6 Check if telemetry is within start / end time of the operation
         - C7 (A)(B) Check if the aircraft complies with deviation thresholds / 4D volume
         - C8 Check if it is near a GeoFence and / breaches one

        """
        now = arrow.now()

        flight_declaration = db_ops.get_flight_declaration_by_id(id=flight_declaration_id)

        # Flight Operation and Flight Authorization exists, create a notifications helper

        operation_start_time = arrow.get(flight_declaration.start_datetime)
        operation_end_time = arrow.get(flight_declaration.end_datetime)

        # C3 check
        try:
            assert flight_declaration.aircraft_id == aircraft_id
        except AssertionError:
            return ConformanceChecksList.C3

        # C4, C5 check
        try:
            assert flight_declaration.state in [
                OPERATION_STATES[1][0],
                OPERATION_STATES[2][0],
            ]
        except AssertionError:
            return ConformanceChecksList.C5

        # C6 check
        try:
            assert is_time_between(
                begin_time=operation_start_time,
                end_time=operation_end_time,
                check_time=now,
            )
        except AssertionError:
            return ConformanceChecksList.C6

        # C7 check : Check if the aircraft is within the 4D volume

        # Construct the boundary of the current operation by getting the operational intent

        # TODO: Cache this so that it need not be done every time
        operational_intent = json.loads(flight_declaration.operational_intent)
        all_volumes = operational_intent["volumes"]
        # The provided telemetry location cast as a Shapely Point
        lng = float(telemetry_location.lng)
        lat = float(telemetry_location.lat)
        rid_location = Point(lng, lat)
        all_polygon_altitudes: List[PolygonAltitude] = []
        for v in all_volumes:
            v4d = cast_to_volume4d(v)
            altitude_lower = v4d.volume.altitude_lower.value
            altitude_upper = v4d.volume.altitude_upper.value
            outline_polygon = v4d.volume.outline_polygon
            point_list = []
            for vertex in outline_polygon.vertices:
                p = Point(vertex.lng, vertex.lat)
                point_list.append(p)
            outline_polygon = Plgn([[p.x, p.y] for p in point_list])

            pa = PolygonAltitude(
                polygon=outline_polygon,
                altitude_upper=altitude_upper,
                altitude_lower=altitude_lower,
            )
            all_polygon_altitudes.append(pa)

        rid_obs_within_all_volumes = []
        rid_obs_within_altitudes = []
        for p in all_polygon_altitudes:
            is_within = rid_location.within(p.polygon)
            # If the aircraft RID is within the the polygon, check the altitude
            altitude_conformant = (
                True if altitude_lower <= altitude_m_wgs_84 <= altitude_upper else False
            )

            rid_obs_within_all_volumes.append(is_within)
            rid_obs_within_altitudes.append(altitude_conformant)

        aircraft_bounds_conformant = any(rid_obs_within_all_volumes)
        aircraft_altitude_conformant = any(rid_obs_within_altitudes)

        try:
            assert aircraft_altitude_conformant
        except AssertionError:
            return ConformanceChecksList.C7a
        try:
            assert aircraft_bounds_conformant
        except AssertionError:
            return ConformanceChecksList.C7b

        # C8 check Check if aircraft is not breaching any active Geofences
        # TODO
        return True

    def check_flight_authorization_conformance(
        self, flight_declaration_id: str
    ) -> bool:
        """This method checks the conformance of a flight authorization independent of telemetry observations being sent:
        C9 a/b Check if telemetry is being sent
        C10 Check operation state that it not ended and the time limit of the flight authorization has passed
        C11 Check if a Flight authorization object exists
        """
        # Flight Operation and Flight Authorization exists, create a notifications helper
        now = arrow.now()
        fd = fdo_models.FlightDeclaration.objects.get(id=flight_declaration_id)
        try:
           fdo_models.FlightAuthorization.objects.get(declaration=fd)
        except fdo_models.FlightAuthorization.DoesNotExist:
            # if flight state is accepted, then change it to ended and delete from dss
            return ConformanceChecksList.C11
        

        # The time the most recent telemetry was sent
        latest_telemetry_datetime = fd.latest_telemetry_datetime
        # Check the current time is within the start / end date time +/- 15 seconds TODO: trim this window as it is to broad
        fifteen_seconds_before_now = now.shift(seconds=-15)
        fifteen_seconds_after_now = now.shift(seconds=15)
        # C10 state check
        # allowed_states = ['Activated', 'Nonconforming', 'Contingent']
        allowed_states = [
            OPERATION_STATES[2][0],
            OPERATION_STATES[3][0],
            OPERATION_STATES[4][0],
        ]
        if fd.state not in allowed_states:
            # set state as ended
            return ConformanceChecksList.C10

        # C9 state check
        # Operation is supposed to start check if telemetry is being submitted (within the last 15 seconds)
        if latest_telemetry_datetime:
            if (
                not fifteen_seconds_before_now
                <= latest_telemetry_datetime
                <= fifteen_seconds_after_now
            ):
                
                return ConformanceChecksList.C9a
        else:
            # declare state as contingent
            return ConformanceChecksList.C9b
        return True
