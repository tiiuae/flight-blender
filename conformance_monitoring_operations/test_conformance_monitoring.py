from django.test import TestCase

from ..conformance_monitoring_operations import operation_states


class OperationStateTests(TestCase):
    def test_state_numbers(self):
        test_inputs = [
            (0, operation_states.ProcessingNotSubmittedToDss),
            (1, operation_states.AcceptedState),
            (2, operation_states.ActivatedState),
            (3, operation_states.NonconformingState),
            (4, operation_states.ContingentState),
            (5, operation_states.EndedState),
            (-1, operation_states.InvalidState),
            (-999, operation_states.InvalidState),
            (999, operation_states.InvalidState),
        ]

        for state_number, expected_state_class in test_inputs:
            operation_state_machine = operation_states.FlightOperationStateMachine(
                state=state_number
            )
            self.assertIsInstance(operation_state_machine.state, expected_state_class)
