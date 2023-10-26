import json
import logging
from dataclasses import asdict
from datetime import timedelta
from os import environ as env

import arrow
from dacite import from_dict
from dotenv import find_dotenv, load_dotenv
from rest_framework import status

from auth_helper.common import get_redis
from common.data_definitions import OPERATION_STATES
from conformance_monitoring_operations.conformance_checks_handler import \
    FlightOperationConformanceHelper
from flight_blender.celery import app
from .models import FlightDeclaration,FlightAuthorization
from notification_operations import notification
from notification_operations.data_definitions import (NotificationLevel,
                                                      NotificationMessage)
from notification_operations.notification_helper import NotificationFactory
from operation_intent.helper import DSSOperationalIntentsCreator
from scd_operations.data_definitions import (
    NotifyPeerUSSPostPayload, OperationalIntentDetailsUSSResponse,
    OperationalIntentStorage, OperationalIntentUSSDetails, SubscriptionState,
    SuccessfulOperationalIntentFlightIDStorage)

logger = logging.getLogger("django")
load_dotenv(find_dotenv())


@app.task(name="_send_flight_approved_message")
def _send_flight_approved_message(
    flight_declaration_id: str,
    message_text: str,
    level: str = NotificationLevel.INFO.value,
    timestamp: str = None,
):
    amqp_connection_url = env.get("AMQP_URL", 0)
    if not amqp_connection_url:
        logger.info("No AMQP URL specified")
        return

    if not timestamp:
        now = arrow.now()
        timestamp = now.isoformat()

    update_message = NotificationMessage(
        body=message_text, level=level, timestamp=timestamp
    )

    my_notification_helper = NotificationFactory(
        flight_declaration_id=flight_declaration_id,
        amqp_connection_url=amqp_connection_url,
    )
    my_notification_helper.declare_queue(
        queue_name="flight-approvals-" + flight_declaration_id
    )
    my_notification_helper.send_message(message_details=update_message)
    logger.info("Submitted Flight Declaration Approval")


@app.task(name="submit_flight_declaration_to_dss")
def submit_flight_declaration_to_dss(flight_declaration_id: str):
    usingDss = env.get("DSS", "false")

    if usingDss == "false":
        fo = FlightDeclaration.objects.get(id=flight_declaration_id)
        # Update state of the flight operation
        fo.state = 1
        id_str = str(fo.id)
        message = {"id": id_str, "approved": True}
        _send_flight_approved_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text=message,
            level=NotificationLevel.INFO.value,
        )
        fo.save()
        return

    my_dss_opint_creator = DSSOperationalIntentsCreator(flight_declaration_id)
    start_end_time_validated = (
        my_dss_opint_creator.validate_flight_declaration_start_end_time()
    )
    logging.info("Flight Operation Validation status %s" % start_end_time_validated)

    if not start_end_time_validated:
        logging.error(
            "Flight Declaration start / end times are not valid, please check the submitted declaration, this operation will not be sent to the DSS for strategic deconfliction"
        )

        validation_not_ok_msg = "Flight Operation with ID {operation_id} did not pass time validation, start and end time may not be ahead of two hours".format(
            operation_id=flight_declaration_id
        )
        notification.send_operational_update_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text=validation_not_ok_msg,
            level=NotificationLevel.ERROR.value,
            log_message="Submitted Flight Declaration Notification",
        )
        return

    validation_ok_msg = "Flight Operation with ID {operation_id} validated for start and end time, submitting to DSS..".format(
        operation_id=flight_declaration_id
    )
    notification.send_operational_update_message.delay(
        flight_declaration_id=flight_declaration_id,
        message_text=validation_ok_msg,
        level=NotificationLevel.INFO.value,
        log_message="Submitted Flight Declaration Notification",
    )

    opint_submission_result = my_dss_opint_creator.submit_flight_declaration_to_dss()

    if opint_submission_result.status_code not in [
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    ]:
        logger.error(
            "Error in submitting Flight Declaration to the DSS %s"
            % opint_submission_result.status
        )

        dss_submission_error_msg = "Flight Operation with ID {operation_id} could not be submitted to the DSS, check the Auth server and / or the DSS URL".format(
            operation_id=flight_declaration_id
        )
        notification.send_operational_update_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text=dss_submission_error_msg,
            level=NotificationLevel.ERROR.value,
            log_message="Submitted Flight Declaration Notification",
        )
        return

    logger.info(
        "Successfully submitted Flight Declaration to the DSS %s"
        % opint_submission_result.status
    )

    submission_success_msg = "Flight Operation with ID {operation_id} submitted successfully to the DSS".format(
        operation_id=flight_declaration_id
    )
    notification.send_operational_update_message.delay(
        flight_declaration_id=flight_declaration_id,
        message_text=submission_success_msg,
        level=NotificationLevel.INFO.value,
        log_message="Submitted Flight Declaration Notification",
    )

    fo = FlightDeclaration.objects.get(id=flight_declaration_id)
    # Update state of the flight operation
    fo.state = 1

    submission_state_updated_msg = "Flight Operation with ID {operation_id} has a updated state: Accepted. ".format(
        operation_id=flight_declaration_id
    )
    notification.send_operational_update_message.delay(
        flight_declaration_id=flight_declaration_id,
        message_text=submission_state_updated_msg,
        level=NotificationLevel.INFO.value,
        log_message="Submitted Flight Declaration Notification",
    )
    fo.save()
    logging.info(
        "Details of the submission status %s" % opint_submission_result.message
    )


#TODO: This function is not async yet!
@app.task(name="submit_flight_declaration_to_dss_async")
def submit_flight_declaration_to_dss_async(flight_declaration_id: str):
    my_dss_opint_creator = DSSOperationalIntentsCreator(flight_declaration_id)
    start_end_time_validated = (
        my_dss_opint_creator.validate_flight_declaration_start_end_time()
    )

    logger.info("Flight Operation Validation status %s" % start_end_time_validated)

    if not start_end_time_validated:
        logger.error(
            "Flight Declaration start / end times are not valid, please check the submitted declaration, this operation will not be sent to the DSS for strategic deconfliction"
        )
        validation_not_ok_msg = "Flight Operation with ID {operation_id} did not pass time validation, start and end time may not be ahead of two hours".format(
            operation_id=flight_declaration_id
        )
        notification.send_operational_update_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text=validation_not_ok_msg,
            level=NotificationLevel.ERROR.value,
        )
        return

    validation_ok_msg = "Flight Operation with ID {operation_id} validated for start and end time, submitting to DSS..".format(
        operation_id=flight_declaration_id
    )
    notification.send_operational_update_message.delay(
        flight_declaration_id=flight_declaration_id,
        message_text=validation_ok_msg,
        level=NotificationLevel.INFO.value,
    )
    logger.info("Submitting to DSS..")

    opint_submission_result = my_dss_opint_creator.submit_flight_declaration_to_dss()

    if opint_submission_result.status_code not in [
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    ]:
        logger.error(
            "Error in submitting Flight Declaration to the DSS %s"
            % opint_submission_result.status
        )
        dss_submission_error_msg = "Flight Operation with ID {operation_id} could not be submitted to the DSS, check the Auth server and / or the DSS URL".format(
            operation_id=flight_declaration_id
        )
        notification.send_operational_update_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text=dss_submission_error_msg,
            level=NotificationLevel.ERROR.value,
        )
        return

    logger.info(
        "Successfully submitted Flight Declaration to the DSS %s"
        % opint_submission_result.status
    )

    submission_success_msg = "Flight Operation with ID {operation_id} submitted successfully to the DSS".format(
        operation_id=flight_declaration_id
    )
    notification.send_operational_update_message.delay(
        flight_declaration_id=flight_declaration_id,
        message_text=submission_success_msg,
        level=NotificationLevel.INFO.value,
    )

    ###### Change via new state check helper
    fd = FlightDeclaration.objects.get(id=flight_declaration_id)
    fa = FlightAuthorization.objects.get(
                declaration=fd
    )
    logger.info("Saving created operational intent details..")
    created_opint = fa.dss_operational_intent_id
    view_r_bounds = fd.bounds
    operational_intent_full_details = OperationalIntentStorage(
        bounds=view_r_bounds,
        start_time=fd.start_datetime.isoformat(),
        end_time=fd.end_datetime.isoformat(),
        alt_max=50,
        alt_min=25,
        success_response=opint_submission_result.dss_response,
        operational_intent_details=json.loads(fd.operational_intent),
    )
    # Store flight ID
    delta = timedelta(seconds=10800)
    flight_opint = "flight_opint." + str(flight_declaration_id)
    r = get_redis()
    r.set(flight_opint, json.dumps(asdict(operational_intent_full_details)))
    r.expire(name=flight_opint, time=delta)

    # Store the details of the operational intent reference
    flight_op_int_storage = SuccessfulOperationalIntentFlightIDStorage(
        operation_id=str(flight_declaration_id), operational_intent_id=created_opint
    )

    #TODO: Make these kind of Redis topic constants.
    opint_flight_ref = "opint_flightref." + created_opint
    r.set(opint_flight_ref, json.dumps(asdict(flight_op_int_storage)))
    r.expire(name=opint_flight_ref, time=delta)
    logger.info("Changing operation state..")
    original_state = fd.state
    accepted_state = OPERATION_STATES[1][0]
    conformance_helper = FlightOperationConformanceHelper(
        flight_declaration_id=flight_declaration_id
    )
    transition_valid = conformance_helper.verify_operation_state_transition(
        original_state=original_state, new_state=accepted_state, event="dss_accepts"
    )
    if transition_valid:
        fd.state = accepted_state
        fd.save()
        logger.info(
            "The state change transition to Accepted state from current state Created is valid.."
        )
        fd.add_state_history_entry(
            new_state=accepted_state,
            original_state=original_state,
            notes="Successfully submitted to the DSS",
        )

        submission_state_updated_msg = "Flight Operation with ID {operation_id} has a updated state: Accepted. ".format(
            operation_id=flight_declaration_id
        )
        notification.send_operational_update_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text=submission_state_updated_msg,
            level=NotificationLevel.INFO.value,
        )

        logger.info(
            "Details of the submission status %s" % opint_submission_result.message
        )

        # TODO: Make it async
        # Notify subscribers of new operational intent
        subscribers = opint_submission_result.dss_response.subscribers
        if not subscribers:
            logger.info("No subscribers found")
            return

        logger.info("Notifying subscribers..")

        for subscriber in subscribers:
            subscriptions_raw = subscriber["subscriptions"]
            uss_base_url = subscriber["uss_base_url"]
            blender_base_url = env.get("BLENDER_FQDN", 0)

            if (
                uss_base_url != blender_base_url
            ):  # There are others who are subscribed, not just ourselves
                subscriptions = from_dict(
                    data_class=SubscriptionState, data=subscriptions_raw
                )
                op_int_details = from_dict(
                    data_class=OperationalIntentUSSDetails,
                    data=json.loads(fd.operational_intent),
                )
                operational_intent = OperationalIntentDetailsUSSResponse(
                    reference=opint_submission_result.dss_response.operational_intent_reference,
                    details=op_int_details,
                )
                post_notification_payload = NotifyPeerUSSPostPayload(
                    operational_intent_id=created_opint,
                    operational_intent=operational_intent,
                    subscriptions=subscriptions,
                )
                # Notify Subscribers
                my_dss_opint_creator.notify_peer_uss(
                    uss_base_url=uss_base_url,
                    notification_payload=post_notification_payload,
                )
