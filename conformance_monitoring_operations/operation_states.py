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


# Start states
class _ProcessingNotSubmittedToDss(_State):
    def on_event(self, event):
        if event == "dss_accepts":
            return _AcceptedState()
        return self


# Start states
class _AcceptedState(_State):
    def on_event(self, event):
        if event == "operator_activates":
            return _ActivatedState()
        elif event == "operator_confirms_ended":
            return _EndedState()
        elif event == "ua_departs_early_late_outside_op_intent":
            return _NonconformingState()

        return self


class _ActivatedState(_State):
    def on_event(self, event):
        if event == "operator_confirms_ended":
            return _EndedState()
        elif event == "ua_exits_coordinated_op_intent":
            return _NonconformingState()
        elif event == "operator_initiates_contingent":
            return _ContingentState()

        return self


class _EndedState(_State):
    def on_event(self, event):
        return self


class _NonconformingState(_State):
    def on_event(self, event):
        if event == "operator_return_to_coordinated_op_intent":
            return _ActivatedState()
        elif event == "operator_confirms_ended":
            return _EndedState()
        elif event in ["timeout", "operator_confirms_contingent"]:
            return _ContingentState()
        return self


class _ContingentState(_State):
    def on_event(self, event):
        if event == "operator_confirms_ended":
            return _EndedState()

        return self


# End states.


class FlightOperationStateMachine(object):
    def __init__(self, state: int = 1):
        s = match_state(state)
        self.state = s

    def on_event(self, event):
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
