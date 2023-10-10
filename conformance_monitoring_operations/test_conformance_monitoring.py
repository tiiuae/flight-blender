from django.test import TestCase

from ..conformance_monitoring_operations import operation_states as os


#os = operation_state
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
            os_machine = os.FlightOperationStateMachine(
                state=state_number
            )
            self.assertIsInstance(os_machine.state, expected_state_class)


    def test_processing_not_submitted_to_dss_state_events(self):
        os_machine = os.FlightOperationStateMachine(
                state=0
            )
        # Some other event
        os_machine.on_event(os.OperationEvent.TIMEOUT)
        self.assertIsInstance(os_machine.state, os.ProcessingNotSubmittedToDss)

        # State only changes when the event is DSS_ACCEPTS
        os_machine.on_event(os.OperationEvent.DSS_ACCEPTS)
        self.assertIsInstance(os_machine.state, os.AcceptedState)


    def test_accepted_state_events(self):
        os_machine = os.FlightOperationStateMachine(
                state=1
            )
        os_machine_1 = os.FlightOperationStateMachine(
                state=1
            )
        os_machine_2 = os.FlightOperationStateMachine(
                state=1
            )
        os_machine_3 = os.FlightOperationStateMachine(
                state=1
            )
        os_machine.on_event(os.OperationEvent.OPERATOR_ACTIVATES)
        self.assertIsInstance(os_machine.state, os.ActivatedState)
        
        os_machine_1.on_event(os.OperationEvent.OPERATOR_CONFIRMS_ENDED)
        self.assertIsInstance(os_machine_1.state, os.EndedState)
        
        os_machine_2.on_event(os.OperationEvent.UA_DEPARTS_EARLY_LATE_OUTSIDE_OP_INTENT)
        self.assertIsInstance(os_machine_2.state, os.NonconformingState)

        os_machine_3.on_event(os.OperationEvent.TIMEOUT)
        self.assertIsInstance(os_machine_3.state, os.AcceptedState)


