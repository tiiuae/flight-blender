import logging
import uuid

import arrow
import tldextract
from dacite import from_dict
from common.data_definitions import OPERATION_STATES
from flight_declaration_operations import models as fdo_models
from rest_framework import status
from scd_operations import dss_scd_helper
from scd_operations.data_definitions import (
    NotifyPeerUSSPostPayload,
    OperationalIntentSubmissionStatus,
)
from .data_definitions import FlightDeclarationOperationalIntentStorageDetails

logger = logging.getLogger("django")

INDEX_NAME = "opint_idx"


class DSSOperationalIntentsCreator:
    """This class provides helper function to submit a operational intent in the DSS based on a operation ID"""

    def __init__(self, flight_declaration_id: str):
        self.flight_declaration_id = flight_declaration_id

    def validate_flight_declaration_start_end_time(self) -> bool:
        flight_declaration = fdo_models.FlightDeclaration.objects.get(
            id=self.flight_declaration_id
        )
        # check that flight declaration start and end time is in the next two hours
        now = arrow.now()
        two_hours_from_now = now.shift(hours=48)

        op_start_time = arrow.get(flight_declaration.start_datetime)
        op_end_time = arrow.get(flight_declaration.end_datetime)

        start_time_ok = op_start_time <= two_hours_from_now and op_start_time >= now
        end_time_ok = op_end_time <= two_hours_from_now and op_end_time >= now

        start_end_time_oks = [start_time_ok, end_time_ok]
        if False in start_end_time_oks:
            return False
        else:
            return True

    def submit_flight_declaration_to_dss(self) -> OperationalIntentSubmissionStatus:
        """This method submits a flight declaration as a operational intent to the DSS"""
        # Get the Flight Declaration object

        new_entity_id = str(uuid.uuid4())
        scd_dss_helper = dss_scd_helper.SCDOperations()

        fd = fdo_models.FlightDeclaration.objects.get(id=self.flight_declaration_id)
        fa = fdo_models.FlightAuthorization.objects.get(declaration=fd)
        operational_intent_data = from_dict(
            data_class=FlightDeclarationOperationalIntentStorageDetails,
            data=fd.operational_intent,
        )

        auth_token = scd_dss_helper.get_auth_token()

        if "error" in auth_token:
            logger.error(
                "Error in retrieving auth_token, check if the auth server is running properly, error details displayed above"
            )
            logger.error(auth_token["error"])
            op_int_submission = OperationalIntentSubmissionStatus(
                status="auth_server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error in getting a token from the Auth server",
                dss_response={},
                operational_intent_id=new_entity_id,
            )
            return op_int_submission

        op_int_submission = (
            scd_dss_helper.create_and_submit_operational_intent_reference(
                state=operational_intent_data.state,
                volumes=operational_intent_data.volumes,
                off_nominal_volumes=operational_intent_data.off_nominal_volumes,
                priority=operational_intent_data.priority,
            )
        )

        # Update flight Authorization and Flight State
        current_state = fd.state
        if op_int_submission.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        ]:
            fa.dss_operational_intent_id = op_int_submission.operational_intent_id
            fa.save()
            # Update operation state
            logger.info("Updating state from Processing to Accepted...")
            accepted_state = OPERATION_STATES[1][0]
            fd.state = accepted_state
            fd.save()
            fd.add_state_history_entry(
                new_state=accepted_state,
                original_state=current_state,
                notes="Operational Intent successfully submitted to DSS and is Accepted",
            )
        # Client errors
        elif 400 <= op_int_submission.status_code < 500:
            error_notes = "Unhandled client exception"
            match op_int_submission.status_code:
                case status.HTTP_400_BAD_REQUEST:
                    error_notes = "Error during submission of operational intent, the DSS rejected because one or more parameters was missing"
                case status.HTTP_409_CONFLICT:
                    error_notes = "Error during submission of operational intent, the DSS rejected it with because the latest airspace keys was not present"
                case status.HTTP_401_UNAUTHORIZED:
                    error_notes = "Error during submission of operational intent, the token was invalid"
                case status.HTTP_403_FORBIDDEN:
                    error_notes = "Error during submission of operational intent, the appropriate scope was not present"
                case status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
                    error_notes = "Error during submission of operational intent,  the operational intent was too large"
                case status.HTTP_429_TOO_MANY_REQUESTS:
                    error_notes = "Error during submission of operational intent, too many requests were submitted to the DSS"
            # Update operation state, the DSS rejected our data
            logger.info(
                "There was a error in submitting the operational intent to the DSS, the DSS rejected our submission with a {status_code} response code".format(
                    status_code=op_int_submission.status_code
                )
            )
            reject_state = OPERATION_STATES[8][0]
            fd.state = reject_state
            fd.save()
            fd.add_state_history_entry(
                new_state=reject_state,
                original_state=current_state,
                notes=error_notes,
            )
        elif (
            op_int_submission.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            and op_int_submission.message == "conflict_with_flight"
        ):
            # Update operation state, DSS responded with a error
            logger.info(
                "Flight is not deconflicted, updating state from Processing to Rejected .."
            )
            current_state = fd.state
            reject_state = OPERATION_STATES[8][0]
            fd.state = reject_state
            fd.save()
            fd.add_state_history_entry(
                new_state=reject_state,
                original_state=current_state,
                notes="Flight was not deconflicted correctly",
            )

        return op_int_submission

    def notify_peer_uss(
        self, uss_base_url: str, notification_payload: NotifyPeerUSSPostPayload
    ):
        """This method submits a flight declaration as a operational intent to the DSS"""
        # Get the Flight Declaration object

        my_scd_dss_helper = dss_scd_helper.SCDOperations()

        try:
            ext = tldextract.extract(uss_base_url)
        except Exception:
            uss_audience = "localhost"
        else:
            if ext.domain in [
                "localhost",
                "internal",
            ]:  # for host.docker.internal type calls
                uss_audience = "localhost"
            else:
                uss_audience = ".".join(
                    ext[:3]
                )  # get the subdomain, domain and suffix and create a audience and get credentials

        my_scd_dss_helper.notify_peer_uss_of_created_updated_operational_intent(
            uss_base_url=uss_base_url,
            notification_payload=notification_payload,
            audience=uss_audience,
        )
