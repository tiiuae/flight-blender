import arrow
import pytest
from django.core import management
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.test import TestCase

from common.data_definitions import OPERATION_STATES
from flight_declaration_operations import models as fdo_models
from scd_operations.data_definitions import LatLngPoint

from ..conformance_monitoring_operations import operation_states as os
from ..conformance_monitoring_operations import utils
from ..conformance_monitoring_operations.conformance_state_checks import (
    ConformanceChecksList,
)


class OperationStateTests(TestCase):
    def test_state_numbers(self):
        test_inputs = [
            (0, os.ProcessingNotSubmittedToDss),
            (1, os.AcceptedState),
            (2, os.ActivatedState),
            (3, os.NonconformingState),
            (4, os.ContingentState),
            (5, os.EndedState),
            (-1, os.InvalidState),
            (-999, os.InvalidState),
            (999, os.InvalidState),
        ]

        for state_number, expected_state_class in test_inputs:
            os_machine = os.FlightOperationStateMachine(state=state_number)
            self.assertIsInstance(os_machine.state, expected_state_class)

    def test_processing_not_submitted_to_dss_state_events(self):
        os_machine = os.FlightOperationStateMachine(state=0)
        # Some other event
        os_machine.on_event(os.OperationEvent.TIMEOUT)
        self.assertIsInstance(os_machine.state, os.ProcessingNotSubmittedToDss)

        # State only changes when the event is DSS_ACCEPTS
        os_machine.on_event(os.OperationEvent.DSS_ACCEPTS)
        self.assertIsInstance(os_machine.state, os.AcceptedState)

    def test_accepted_state_events(self):
        os_machine = os.FlightOperationStateMachine(state=1)
        os_machine_1 = os.FlightOperationStateMachine(state=1)
        os_machine_2 = os.FlightOperationStateMachine(state=1)
        os_machine_3 = os.FlightOperationStateMachine(state=1)
        os_machine.on_event(os.OperationEvent.OPERATOR_ACTIVATES)
        self.assertIsInstance(os_machine.state, os.ActivatedState)

        os_machine_1.on_event(os.OperationEvent.OPERATOR_CONFIRMS_ENDED)
        self.assertIsInstance(os_machine_1.state, os.EndedState)

        os_machine_2.on_event(os.OperationEvent.UA_DEPARTS_EARLY_LATE_OUTSIDE_OP_INTENT)
        self.assertIsInstance(os_machine_2.state, os.NonconformingState)

        os_machine_3.on_event(os.OperationEvent.TIMEOUT)
        self.assertIsInstance(os_machine_3.state, os.AcceptedState)

    def test_activated_state_events(self):
        os_machine = os.FlightOperationStateMachine(state=2)
        os_machine_1 = os.FlightOperationStateMachine(state=2)
        os_machine_2 = os.FlightOperationStateMachine(state=2)
        os_machine_3 = os.FlightOperationStateMachine(state=2)
        os_machine.on_event(os.OperationEvent.UA_EXITS_COORDINATED_OP_INTENT)
        self.assertIsInstance(os_machine.state, os.NonconformingState)

        os_machine_1.on_event(os.OperationEvent.OPERATOR_CONFIRMS_ENDED)
        self.assertIsInstance(os_machine_1.state, os.EndedState)

        os_machine_2.on_event(os.OperationEvent.OPERATOR_INITIATES_CONTINGENT)
        self.assertIsInstance(os_machine_2.state, os.ContingentState)

        os_machine_3.on_event(os.OperationEvent.TIMEOUT)
        self.assertIsInstance(os_machine_3.state, os.ActivatedState)

    def test_nonconforming_state_events(self):
        os_machine = os.FlightOperationStateMachine(state=3)
        os_machine_1 = os.FlightOperationStateMachine(state=3)
        os_machine_2 = os.FlightOperationStateMachine(state=3)
        os_machine_3 = os.FlightOperationStateMachine(state=3)
        os_machine_4 = os.FlightOperationStateMachine(state=3)
        os_machine.on_event(os.OperationEvent.OPERATOR_RETURN_TO_COORDINATED_OP_INTENT)
        self.assertIsInstance(os_machine.state, os.ActivatedState)

        os_machine_1.on_event(os.OperationEvent.OPERATOR_CONFIRMS_ENDED)
        self.assertIsInstance(os_machine_1.state, os.EndedState)

        os_machine_2.on_event(os.OperationEvent.TIMEOUT)
        self.assertIsInstance(os_machine_2.state, os.ContingentState)

        os_machine_3.on_event(os.OperationEvent.OPERATOR_CONFIRMS_CONTINGENT)
        self.assertIsInstance(os_machine_3.state, os.ContingentState)

        os_machine_4.on_event(os.OperationEvent.DSS_ACCEPTS)
        self.assertIsInstance(os_machine_4.state, os.NonconformingState)

    def test_contingent_state_events(self):
        os_machine = os.FlightOperationStateMachine(state=4)
        os_machine_1 = os.FlightOperationStateMachine(state=4)
        os_machine_2 = os.FlightOperationStateMachine(state=4)
        os_machine.on_event(os.OperationEvent.OPERATOR_CONFIRMS_ENDED)
        self.assertIsInstance(os_machine.state, os.EndedState)

        os_machine_1.on_event(os.OperationEvent.TIMEOUT)
        self.assertIsInstance(os_machine_1.state, os.ContingentState)

        os_machine_2.on_event(os.OperationEvent.UA_EXITS_COORDINATED_OP_INTENT)
        self.assertIsInstance(os_machine_2.state, os.ContingentState)

    def test_get_status_number_by_class(self):
        test_inputs = [
            (os.ProcessingNotSubmittedToDss, 0),
            (os.AcceptedState, 1),
            (os.ActivatedState, 2),
            (os.NonconformingState, 3),
            (os.ContingentState, 4),
            (os.EndedState, 5),
            (os.InvalidState, -1),
        ]
        for state_class, expected_state_number in test_inputs:
            state_number = os.get_status(state=state_class())
            self.assertEqual(state_number, expected_state_number)

    def test_ended_invalid_states_event_changes(self):
        os_machine = os.FlightOperationStateMachine(state=5)
        os_machine.on_event(os.OperationEvent.OPERATOR_RETURN_TO_COORDINATED_OP_INTENT)
        self.assertIsInstance(os_machine.state, os.EndedState)

        os_machine1 = os.FlightOperationStateMachine(state=-1)
        os_machine1.on_event(os.OperationEvent.OPERATOR_RETURN_TO_COORDINATED_OP_INTENT)
        self.assertIsInstance(os_machine1.state, os.InvalidState)


# TODO Not all logics are covered yet
# Tests for management/commands/
class MgmtCmdsOperatorDeclaresContingencyTests(TestCase):
    def test_no_flight_declaration_id(self):
        with pytest.raises(
            CommandError,
            match=r"Incomplete command, Flight Declaration ID not provided",
        ):
            management.call_command(
                "operator_declares_contingency",
                dry_run=0,
            )

    def test_invalid_uuid(self):
        with pytest.raises(ValidationError, match=r"['“001” is not a valid UUID.']"):
            management.call_command(
                "operator_declares_contingency",
                flight_declaration_id="001",
                dry_run=0,
            )

    def test_non_existent_uuid(self):
        with pytest.raises(
            CommandError,
            match=r"Flight Declaration with ID 2e0f965b-c511-43c9-8a9c-8599533bee43 does not exist",
        ):
            management.call_command(
                "operator_declares_contingency",
                flight_declaration_id="2e0f965b-c511-43c9-8a9c-8599533bee43",
                dry_run=0,
            )


class FlightAuthorizationConformantTests(TestCase):
    @pytest.mark.usefixtures("submit_flight_plan_for_conformance_monitoring_no_auth")
    def test_flight_authorization_conformance_no_authorization(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)

        # Check Flight authorization conformance
        conformance_ops = utils.BlenderConformanceEngine()
        flight_authorization_conformant = (
            conformance_ops.check_flight_authorization_conformance(
                flight_declaration_id=fd.id
            )
        )
        # C11: No Flight Authorization
        self.assertEqual(flight_authorization_conformant, ConformanceChecksList.C11)

    @pytest.mark.usefixtures("submit_flight_plan_for_conformance_monitoring_with_auth")
    def test_flight_authorization_conformance_invalid_state(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)

        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)

        # Check Flight authorization conformance
        conformance_ops = utils.BlenderConformanceEngine()
        flight_authorization_conformant = (
            conformance_ops.check_flight_authorization_conformance(
                flight_declaration_id=fd.id
            )
        )
        # C10: State not in accepted, non-conforming, activated
        self.assertEqual(flight_authorization_conformant, ConformanceChecksList.C10)

    @pytest.mark.usefixtures("submit_flight_plan_for_conformance_monitoring_with_auth")
    def test_flight_authorization_conformance_no_telemetry(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)
        fd.state = OPERATION_STATES[2][0]  # Activate the flight
        fd.save()
        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)
        # Check Flight authorization conformance
        conformance_ops = utils.BlenderConformanceEngine()
        flight_authorization_conformant = (
            conformance_ops.check_flight_authorization_conformance(
                flight_declaration_id=fd.id
            )
        )
        # C9a: Telemetry not received
        self.assertEqual(flight_authorization_conformant, ConformanceChecksList.C9a)

    @pytest.mark.usefixtures("submit_flight_plan_for_conformance_monitoring_with_auth")
    def test_flight_authorization_conformance_no_telemetry_within_15_seconds(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)
        fd.state = OPERATION_STATES[2][0]  # Activate the flight
        now = arrow.now()
        fd.latest_telemetry_datetime = now.shift(seconds=-20).isoformat()
        fd.save()
        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)
        # Check Flight authorization conformance
        conformance_ops = utils.BlenderConformanceEngine()
        flight_authorization_conformant = (
            conformance_ops.check_flight_authorization_conformance(
                flight_declaration_id=fd.id
            )
        )
        # C9b: Telemetry not received within last 15 secs
        self.assertEqual(flight_authorization_conformant, ConformanceChecksList.C9b)

    @pytest.mark.usefixtures("submit_flight_plan_for_conformance_monitoring_with_auth")
    def test_flight_authorization_conformance_valid(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)
        fd.state = OPERATION_STATES[2][0]  # Activate the flight
        now = arrow.now()
        fd.latest_telemetry_datetime = now.shift(seconds=-5).isoformat()
        fd.save()
        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)
        # Check Flight authorization conformance
        conformance_ops = utils.BlenderConformanceEngine()
        flight_authorization_conformant = (
            conformance_ops.check_flight_authorization_conformance(
                flight_declaration_id=fd.id
            )
        )
        # Flight is conformance in terms of FLight Authorization checks
        self.assertEqual(flight_authorization_conformant, True)


class FlightOperationConformantTests(TestCase):
    @pytest.mark.usefixtures("submit_flight_plan_for_conformance_monitoring_with_auth")
    def test_operation_conformance_invalid_aircraft_id(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)

        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)

        conformance_ops = utils.BlenderConformanceEngine()
        conformant_via_telemetry = (
            conformance_ops.is_operation_conformant_via_telemetry(
                flight_declaration_id=fd.id,
                aircraft_id="111111",
                telemetry_location=LatLngPoint(lat=0, lng=0),
                altitude_m_wgs_84=float(0),
            )
        )

        # C3: Telemetry Auth mismatch
        self.assertEqual(conformant_via_telemetry, ConformanceChecksList.C3)

    @pytest.mark.usefixtures("submit_flight_plan_for_conformance_monitoring_with_auth")
    def test_operation_conformance_invalid_state(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)
        fd.state = OPERATION_STATES[6][0]
        fd.save()

        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)

        conformance_ops = utils.BlenderConformanceEngine()
        conformant_via_telemetry = (
            conformance_ops.is_operation_conformant_via_telemetry(
                flight_declaration_id=fd.id,
                aircraft_id="990099",  # This value is from conftest record
                telemetry_location=LatLngPoint(lat=0, lng=0),
                altitude_m_wgs_84=float(0),
            )
        )

        # C4: Operation state invalid
        self.assertEqual(conformant_via_telemetry, ConformanceChecksList.C4)

    @pytest.mark.usefixtures("submit_flight_plan_for_conformance_monitoring_with_auth")
    def test_operation_conformance_flight_not_activated(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)
        fd.state = OPERATION_STATES[1][0]
        fd.save()

        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)

        conformance_ops = utils.BlenderConformanceEngine()
        conformant_via_telemetry = (
            conformance_ops.is_operation_conformant_via_telemetry(
                flight_declaration_id=fd.id,
                aircraft_id="990099",  # This value is from conftest record
                telemetry_location=LatLngPoint(lat=0, lng=0),
                altitude_m_wgs_84=float(0),
            )
        )

        # C5: Operation not activated
        self.assertEqual(conformant_via_telemetry, ConformanceChecksList.C5)

    @pytest.mark.usefixtures("submit_flight_plan_for_conformance_monitoring_with_auth")
    def test_operation_conformance_flight_invalid_telemetry_time(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)
        fd.state = OPERATION_STATES[2][0]
        fd.save()

        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)

        conformance_ops = utils.BlenderConformanceEngine()
        conformant_via_telemetry = (
            conformance_ops.is_operation_conformant_via_telemetry(
                flight_declaration_id=fd.id,
                aircraft_id="990099",  # This value is from conftest record
                telemetry_location=LatLngPoint(lat=0, lng=0),
                altitude_m_wgs_84=float(0),
            )
        )

        # C6: Telemetry time incorrect
        self.assertEqual(conformant_via_telemetry, ConformanceChecksList.C6)

    # Submits a flight plan with real time!
    @pytest.mark.usefixtures(
        "submit_real_time_flight_plan_for_conformance_monitoring_with_auth"
    )
    def test_operation_conformance_flight_invalid_altitude(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)
        fd.state = OPERATION_STATES[2][0]
        fd.save()

        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)

        conformance_ops = utils.BlenderConformanceEngine()
        conformant_via_telemetry = (
            conformance_ops.is_operation_conformant_via_telemetry(
                flight_declaration_id=fd.id,
                aircraft_id="990099",  # This value is from conftest record
                telemetry_location=LatLngPoint(lat=3, lng=6),
                altitude_m_wgs_84=float(12),  # Altitude must be within 90-100
            )
        )

        # C7b: Flight altitude out of bounds
        self.assertEqual(conformant_via_telemetry, ConformanceChecksList.C7b)

    # Submits a flight plan with real time!
    @pytest.mark.usefixtures(
        "submit_real_time_flight_plan_for_conformance_monitoring_with_auth"
    )
    def test_operation_conformance_flight_invalid_bounds(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)
        fd.state = OPERATION_STATES[2][0]
        fd.save()

        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)

        conformance_ops = utils.BlenderConformanceEngine()
        conformant_via_telemetry = (
            conformance_ops.is_operation_conformant_via_telemetry(
                flight_declaration_id=fd.id,
                aircraft_id="990099",  # This value is from conftest record
                telemetry_location=LatLngPoint(lat=1.0, lng=1.0),
                altitude_m_wgs_84=float(95),  # Altitude must be within 90-100
            )
        )

        # C7a: Flight out of bounds
        self.assertEqual(conformant_via_telemetry, ConformanceChecksList.C7a)

    # Submits a flight plan with real time!
    @pytest.mark.usefixtures(
        "submit_real_time_flight_plan_for_conformance_monitoring_with_auth"
    )
    def test_operation_conformance_flight_valid(self):
        fd = fdo_models.FlightDeclaration.objects.filter().first()
        self.assertIsNotNone(fd.id)
        fd.state = OPERATION_STATES[2][0]
        fd.save()

        fa = fdo_models.FlightAuthorization.objects.filter().first()
        self.assertIsNotNone(fa.id)

        conformance_ops = utils.BlenderConformanceEngine()
        conformant_via_telemetry = (
            conformance_ops.is_operation_conformant_via_telemetry(
                flight_declaration_id=fd.id,
                aircraft_id="990099",  # This value is from conftest record
                telemetry_location=LatLngPoint(
                    lat=46.9885, lng=7.4707
                ),  # Telemetry location should be within valid Point
                altitude_m_wgs_84=float(95),  # Altitude must be within 90-100
            )
        )
        # Flight is conformance in terms of FLight Operation checks
        self.assertEqual(conformant_via_telemetry, True)


class ConformanceStateCheckTests(TestCase):
    def test_multiple_state_ids(self):
        invalid_non_conformance_state_id = 0

        with pytest.raises(ValueError, match="Key not found"):
            ConformanceChecksList.state_code(invalid_non_conformance_state_id)

        invalid_non_conformance_state_id = "12"

        with pytest.raises(ValueError, match="Key not found"):
            ConformanceChecksList.state_code(invalid_non_conformance_state_id)

        invalid_non_conformance_state_id = None

        with pytest.raises(ValueError, match="Key not found"):
            ConformanceChecksList.state_code(invalid_non_conformance_state_id)

        valid_non_conformance_state_id = ConformanceChecksList.C10
        non_conformance_state_code = ConformanceChecksList.state_code(
            valid_non_conformance_state_id
        )
        self.assertEqual(valid_non_conformance_state_id, 12)
        self.assertEqual(non_conformance_state_code, "C10")

        valid_non_conformance_state_id = ConformanceChecksList.C2
        non_conformance_state_code = ConformanceChecksList.state_code(
            valid_non_conformance_state_id
        )
        self.assertEqual(valid_non_conformance_state_id, 2)
        self.assertEqual(non_conformance_state_code, "C2")

        valid_non_conformance_state_id = ConformanceChecksList.C7a
        non_conformance_state_code = ConformanceChecksList.state_code(
            valid_non_conformance_state_id
        )
        self.assertEqual(valid_non_conformance_state_id, 7)
        self.assertEqual(non_conformance_state_code, "C7a")

        valid_non_conformance_state_id = ConformanceChecksList.C9b
        non_conformance_state_code = ConformanceChecksList.state_code(
            valid_non_conformance_state_id
        )
        self.assertEqual(valid_non_conformance_state_id, 11)
        self.assertEqual(non_conformance_state_code, "C9b")
