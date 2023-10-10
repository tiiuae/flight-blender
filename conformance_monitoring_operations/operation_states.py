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


class _State(object):
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


class _ProcessingNotSubmittedToDss(_State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.DSS_ACCEPTS:
            return _AcceptedState()
        return self


class _AcceptedState(_State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.OPERATOR_ACTIVATES:
            return _ActivatedState()
        elif event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
            return _EndedState()
        elif event == OperationEvent.UA_DEPARTS_EARLY_LATE_OUTSIDE_OP_INTENT:
            return _NonconformingState()

        return self


class _ActivatedState(_State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
            return _EndedState()
        elif event == OperationEvent.UA_EXITS_COORDINATED_OP_INTENT:
            return _NonconformingState()
        elif event == OperationEvent.OPERATOR_INITIATES_CONTINGENT:
            return _ContingentState()

        return self


class _EndedState(_State):
    def on_event(self):
        return self


class _NonconformingState(_State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.OPERATOR_RETURN_TO_COORDINATED_OP_INTENT:
            return _ActivatedState()
        elif event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
            return _EndedState()
        elif event in [
            OperationEvent.TIMEOUT,
            OperationEvent.OPERATOR_CONFIRMS_CONTINGENT,
        ]:
            return _ContingentState()
        return self


class _ContingentState(_State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
            return _EndedState()

        return self


class FlightOperationStateMachine(object):
    def __init__(self, state: int = 1):
        s = match_state(state)
        self.state = s

    def on_event(self, event: OperationEvent):
        self.state = self.state.on_event(event)


def match_state(status: int):
    if status == 0:
        return _ProcessingNotSubmittedToDss()
    elif status == 1:
        return _AcceptedState()
    elif status == 2:
        return _ActivatedState()
    elif status == 3:
        return _NonconformingState()
    elif status == 4:
        return _ContingentState()
    elif status == 5:
        return _EndedState()
    else:
        return False


def get_status(state: _State):
    if isinstance(state, _ProcessingNotSubmittedToDss):
        return 0
    if isinstance(state, _AcceptedState):
        return 1
    elif isinstance(state, _ActivatedState):
        return 2
    elif isinstance(state, _NonconformingState):
        return 3
    elif isinstance(state, _ContingentState):
        return 4
    elif isinstance(state, _EndedState):
        return 5
    else:
        return False
