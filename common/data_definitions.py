from enum import Enum

from django.utils.translation import gettext_lazy as _


class OperationEvent(Enum):
    DSS_ACCEPTS = "dss_accepts"
    OPERATOR_ACTIVATES = "operator_activates"
    OPERATOR_CONFIRMS_ENDED = "operator_confirms_ended"
    UA_DEPARTS_EARLY_LATE_OUTSIDE_OP_INTENT = "ua_departs_early_late_outside_op_intent"
    UA_EXITS_COORDINATED_OP_INTENT = "ua_exits_coordinated_op_intent"
    OPERATOR_INITIATES_CONTINGENT = "operator_initiates_contingent"
    OPERATOR_RETURN_TO_COORDINATED_OP_INTENT = (
        "operator_return_to_coordinated_op_intent"
    )
    OPERATOR_CONFIRMS_CONTINGENT = "operator_confirms_contingent"
    BLENDER_CONFIRMS_CONTINGENT = "blender_confirms_contingent"
    TIMEOUT = "timeout"


OPERATION_STATES = (
    (0, _("Not Submitted")),
    (1, _("Accepted")),
    (2, _("Activated")),
    (3, _("Nonconforming")),
    (4, _("Contingent")),
    (5, _("Ended")),
    (6, _("Withdrawn")),
    (7, _("Cancelled")),
    (8, _("Rejected")),
)

# This is only used int he SCD Test harness therefore it is partial
OPERATION_STATES_LOOKUP = {
    "Accepted": 1,
    "Activated": 2,
}

OPERATION_TYPES = (
    (1, _("VLOS")),
    (2, _("BVLOS")),
    (3, _("CREWED")),
)


# When an operator changes a states, he / she puts a new state (via the API), this object specifies the event when a operator takes action
OPERATOR_EVENT_LOOKUP = {
    5: OperationEvent.OPERATOR_CONFIRMS_ENDED,
    2: OperationEvent.OPERATOR_ACTIVATES,
    4: OperationEvent.OPERATOR_INITIATES_CONTINGENT,
}
