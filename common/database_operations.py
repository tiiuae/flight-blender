from flight_declaration_operations.models import (
    FlightDeclaration,
)
from conformance_monitoring_operations.models import TaskScheduler
from typing import Tuple, List
from uuid import uuid4
import arrow
from django.db.utils import IntegrityError
# from scd_operations.data_definitions import FlightDeclarationCreationPayload
import os
import json
from dataclasses import asdict
import logging
from scd_operations.data_definitions import PartialCreateOperationalIntentReference
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger("django")


load_dotenv(find_dotenv())

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


class BlenderDatabaseReader:
    """
    A file to unify read and write operations to the database. Eventually caching etc. can be added via this file
    """
    def check_flight_declaration_exists(self, flight_declaration_id: str) -> bool:
        return FlightDeclaration.objects.filter(id=flight_declaration_id).exists()

    def get_current_flight_declaration_ids(self, now: str) -> Tuple[None, uuid4]:
        """This method gets flight operation ids that are active in the system within near the time interval"""
        n = arrow.get(now)

        two_minutes_before_now = n.shift(seconds=-120).isoformat()
        five_hours_from_now = n.shift(minutes=300).isoformat()
        relevant_ids = FlightDeclaration.objects.filter(
            start_datetime__gte=two_minutes_before_now,
            end_datetime__lte=five_hours_from_now,
        ).values_list("id", flat=True)
        return relevant_ids

    def get_current_flight_accepted_activated_declaration_ids(
        self, now: str
    ) -> Tuple[None, uuid4]:
        """This method gets flight operation ids that are active in the system"""
        n = arrow.get(now)

        two_minutes_before_now = n.shift(seconds=-120).isoformat()
        five_hours_from_now = n.shift(minutes=300).isoformat()
        relevant_ids = (
            FlightDeclaration.objects.filter(
                start_datetime__gte=two_minutes_before_now,
                end_datetime__lte=five_hours_from_now,
            )
            .filter(state__in=[1, 2])
            .values_list("id", flat=True)
        )
        return relevant_ids

    def get_conformance_monitoring_task(
        self, flight_declaration: FlightDeclaration
    ) -> Tuple[None, TaskScheduler]:
        try:
            return TaskScheduler.objects.get(flight_declaration=flight_declaration)
        except TaskScheduler.DoesNotExist:
            return None


class BlenderDatabaseWriter:
    def delete_flight_declaration(self, flight_declaration_id: str) -> bool:
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            flight_declaration.delete()
            return True
        except FlightDeclaration.DoesNotExist:
            return False
        except IntegrityError as ie:
            return False

    def create_flight_declaration(
        self, flight_declaration_creation
    ) -> bool:
        try:
            flight_declaration = FlightDeclaration(
                id=flight_declaration_creation.id,
                operational_intent=flight_declaration_creation.operational_intent,
                flight_declaration_raw_geojson=flight_declaration_creation.flight_declaration_raw_geojson,
                bounds=flight_declaration_creation.bounds,
                aircraft_id=flight_declaration_creation.aircraft_id,
                state=flight_declaration_creation.state,
            )
            flight_declaration.save()
            return True

        except IntegrityError as ie:
            return False


    def update_telemetry_timestamp(self, flight_declaration_id: str) -> bool:
        now = arrow.now().isoformat()
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            flight_declaration.latest_telemetry_datetime = now
            flight_declaration.save()
            return True
        except FlightDeclaration.DoesNotExist:
            return False

    def update_flight_operation_operational_intent(
        self,
        flight_declaration_id: str,
        operational_intent: PartialCreateOperationalIntentReference,
    ) -> bool:
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            flight_declaration.operational_intent = json.dumps(
                asdict(operational_intent)
            )
            # TODO: Convert the updated operational intent to GeoJSON
            flight_declaration.save()
            return True
        except Exception as e:
            return False

    def create_conformance_monitoring_periodic_task(
        self, flight_declaration: FlightDeclaration
    ) -> bool:
        conformance_monitoring_job = TaskScheduler()
        every = int(os.getenv("HEARTBEAT_RATE_SECS", default=5))
        now = arrow.now()
        fd_end = arrow.get(flight_declaration.end_datetime)
        delta = fd_end - now
        delta_seconds = delta.total_seconds()
        expires = now.shift(seconds=delta_seconds)
        task_name = "check_flight_conformance"

        try:
            p_task = conformance_monitoring_job.schedule_every(
                task_name=task_name,
                period="seconds",
                every=every,
                expires=expires,
                flight_declaration=flight_declaration,
            )
            p_task.start()
            return True
        except Exception as e:
            logger.error()
            return False

    def remove_conformance_monitoring_periodic_task(
        self, conformance_monitoring_task: TaskScheduler
    ):
        conformance_monitoring_task.terminate()
