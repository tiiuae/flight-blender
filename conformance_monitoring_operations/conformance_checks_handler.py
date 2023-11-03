import logging
import os
from os import environ as env

from common.database_operations import BlenderDatabaseReader, BlenderDatabaseWriter
from django.core import management
from dotenv import find_dotenv, load_dotenv
from .operation_states import FlightOperationStateMachine, get_status
from conformance_monitoring_operations import db_operations as db_ops
from common.data_definitions import OperationEvent
load_dotenv(find_dotenv())

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger("django")


class FlightOperationConformanceHelper:
    """
    This class handles changes / transitions to a operation when the conformance check fails, it transitions
    """

    def __init__(self, flight_declaration_id: str):
        self.flight_declaration_id = flight_declaration_id
        self.database_reader = BlenderDatabaseReader()
        self.flight_declaration =  db_ops.get_flight_declaration_by_id(id=flight_declaration_id)
        self.database_writer = BlenderDatabaseWriter()
        self.ENABLE_CONFORMANCE_MONITORING = int(
            os.getenv("ENABLE_CONFORMANCE_MONITORING", 0)
        )
        self.USSP_NETWORK_ENABLED = int(env.get("USSP_NETWORK_ENABLED", 0))

    def verify_operation_state_transition(
        self, original_state: int, new_state: int, event: str
    ) -> bool:
        """
        This class updates the state of a flight operation.
        """
        operation_state_machine = FlightOperationStateMachine(state=original_state)
        logger.info("Current Operation State %s" % operation_state_machine.state)
        operation_state_machine.on_event(event)
        new_state = get_status(operation_state_machine.state)
        if original_state == new_state:
            ## The event cannot trigger a change of state, flight state is not updated
            logger.info("State change verification failed")
            return False
        else:
            return True

    def manage_operation_state_transition(
        self, original_state: int, new_state: int, event: str
    ):
        """
        This method manages the communication with DSS once a new state has been received by the POST method
        """
        if new_state == 5:  # operation has ended
            if event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
                if self.USSP_NETWORK_ENABLED:
                    management.call_command(
                        "operation_ended_clear_dss",
                        flight_declaration_id=self.flight_declaration_id,
                        dry_run=0,
                    )

                if self.ENABLE_CONFORMANCE_MONITORING:
                    # Remove the conformance monitoring periodic job
                    conformance_monitoring_job = (
                        self.database_reader.get_conformance_monitoring_task(
                            flight_declaration=self.flight_declaration
                        )
                    )
                    if conformance_monitoring_job:
                        self.database_writer.remove_conformance_monitoring_periodic_task(
                            conformance_monitoring_task=conformance_monitoring_job
                        )

        elif new_state == 4:  # handle entry into contingent state
            if original_state == 2 and event in [
                OperationEvent.OPERATOR_INITIATES_CONTINGENT,
                OperationEvent.BLENDER_CONFIRMS_CONTINGENT,
            ]:
                # Operator activates contingent state from Activated state
                if self.USSP_NETWORK_ENABLED:
                    management.call_command(
                        "operator_declares_contingency",
                        flight_declaration_id=self.flight_declaration_id,
                        dry_run=0,
                    )

            elif original_state == 3 and event in [
                OperationEvent.TIMEOUT,
                OperationEvent.OPERATOR_CONFIRMS_CONTINGENT,
            ]:
                # Operator activates contingent state / timeout from Non-conforming state
                if self.USSP_NETWORK_ENABLED:
                    management.call_command(
                        "operator_declares_contingency",
                        flight_declaration_id=self.flight_declaration_id,
                        dry_run=0,
                    )

        elif new_state == 3:  # handle entry in non-conforming state
            if event == OperationEvent.UA_EXITS_COORDINATED_OP_INTENT and original_state in [1, 2]:
                # Enters non-conforming from Accepted
                # Command: Update / expand volumes, if DSS is present
                if self.USSP_NETWORK_ENABLED:
                    management.call_command(
                        "update_operational_intent_to_non_conforming_update_expand_volumes",
                        flight_declaration_id=self.flight_declaration_id,
                        dry_run=0,
                    )

            elif event == OperationEvent.UA_DEPARTS_EARLY_LATE_OUTSIDE_OP_INTENT and original_state in [1, 2]:
                # Enters non-conforming from Accepted
                # Command: declare non-conforming, no need to update volumes
                if self.USSP_NETWORK_ENABLED:
                    management.call_command(
                        "update_operational_intent_to_non_conforming",
                        flight_declaration_id=self.flight_declaration_id,
                        dry_run=0,
                    )

        elif new_state == 2:  # handle entry into activated state
            if original_state == 1 and event == OperationEvent.OPERATOR_ACTIVATES:
                # Operator activates accepted state to Activated state
                if self.USSP_NETWORK_ENABLED:
                    management.call_command(
                        "update_operational_intent_to_activated",
                        flight_declaration_id=self.flight_declaration_id,
                        dry_run=0,
                    )
                if self.ENABLE_CONFORMANCE_MONITORING:
                    conformance_monitoring_job = self.database_writer.create_conformance_monitoring_periodic_task(
                        flight_declaration=self.flight_declaration
                    )
                    if conformance_monitoring_job:
                        logger.info(
                            "Created conformance monitoring job for {flight_declaration_id}".format(
                                flight_declaration_id=self.flight_declaration_id
                            )
                        )
                    else:
                        logger.info(
                            "Error in creating conformance monitoring job for {flight_declaration_id}".format(
                                flight_declaration_id=self.flight_declaration_id
                            )
                        )
