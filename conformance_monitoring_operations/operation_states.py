from enum import Enum


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
    TIMEOUT = "timeout"


class State(object):
    """
    A object to hold state transitions as defined in the ASTM F3548-21 standard
    Source: https://dev.to/karn/building-a-simple-state-machine-in-python
    """

    def __init__(self):
        print("Processing current state:%s" % str(self))

    def get_value(self):
        return self._value

    def on_event(self, event):
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__


class ProcessingNotSubmittedToDss(State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.DSS_ACCEPTS:
            return AcceptedState()
        return self


class AcceptedState(State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.OPERATOR_ACTIVATES:
            return ActivatedState()
        elif event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
            return EndedState()
        elif event == OperationEvent.UA_DEPARTS_EARLY_LATE_OUTSIDE_OP_INTENT:
            return NonconformingState()

        return self


class ActivatedState(State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
            return EndedState()
        elif event == OperationEvent.UA_EXITS_COORDINATED_OP_INTENT:
            return NonconformingState()
        elif event == OperationEvent.OPERATOR_INITIATES_CONTINGENT:
            return ContingentState()

        return self


class EndedState(State):
    def on_event(self):
        return self

# Use this when the state number is not within the given standard numbers. eg : -1,999
class InvalidState(State):
    def on_event(self):
        return self

class NonconformingState(State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.OPERATOR_RETURN_TO_COORDINATED_OP_INTENT:
            return ActivatedState()
        elif event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
            return EndedState()
        elif event in [
            OperationEvent.TIMEOUT,
            OperationEvent.OPERATOR_CONFIRMS_CONTINGENT,
        ]:
            return ContingentState()
        return self


class ContingentState(State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
            return EndedState()

        return self


class FlightOperationStateMachine(object):
    def __init__(self, state: int = 1):
        s = _match_state(state)
        self.state = s

    def on_event(self, event: OperationEvent):
        self.state = self.state.on_event(event)


def _match_state(status: int):
    if status == 0:
        return ProcessingNotSubmittedToDss()
    elif status == 1:
        return AcceptedState()
    elif status == 2:
        return ActivatedState()
    elif status == 3:
        return NonconformingState()
    elif status == 4:
        return ContingentState()
    elif status == 5:
        return EndedState()
    else:
        return InvalidState()


def get_status(state: State):
    if isinstance(state, ProcessingNotSubmittedToDss):
        return 0
    if isinstance(state, AcceptedState):
        return 1
    elif isinstance(state, ActivatedState):
        return 2
    elif isinstance(state, NonconformingState):
        return 3
    elif isinstance(state, ContingentState):
        return 4
    elif isinstance(state, EndedState):
        return 5
    else:
        return False
