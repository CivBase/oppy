from mock import call, Mock

from oppy.circuit import circuitmanager as cm
from oppy.circuit.circuitmanager import CircuitManager
from test.utils import BaseTestCase, patch_object


class CircuitManagerCircuitOpenedTestCase(BaseTestCase):
    def setUp(self):
        super(CircuitManagerCircuitOpenedTestCase, self).setUp()
        self.cm = CircuitManager()
        self.mock_logging = patch_object(cm, 'logging').start()
        self.mock_assign_possible_pending_requests = patch_object(
            self.cm, '_assignPossiblePendingRequests').start()

    def test_circuit_opened_no_reference(self):
        self.cm._pending_circuit_map = {}

        self.cm.circuitOpened(Mock(circuit_id='test_id'))

        self.mock_logging.debug.assert_has_calls([
            call('Circuit manager notified that circuit test_id opened.'),
            call('Circuit manager was notified circuit test_id opened, but '
                 'manager has no reference to this circuit.')])

        self.assertFalse(self.mock_assign_possible_pending_requests.called)
        self.assertFalse(self.mock_logging.info.called)

    def test_circuit_opened_sent_open_message(self):
        self.cm._pending_circuit_map = {'test_id': 'value'}
        self.cm._sent_open_message = True
        circuit = Mock(circuit_id='test_id')

        self.cm.circuitOpened(circuit)

        self.assertEqual(self.cm._open_circuit_map['test_id'], circuit)
        self.assertTrue(self.cm._sent_open_message)
        self.mock_logging.debug.assert_called_once_with(
            'Circuit manager notified that circuit test_id opened.')

        self.mock_assign_possible_pending_requests.assert_called_once_with(
            circuit)

        self.assertFalse(self.mock_logging.info.called)

    def test_circuit_opened_not_sent_open_message(self):
        self.cm._pending_circuit_map = {'test_id': 'value'}
        self.cm._sent_open_message = False
        circuit = Mock(circuit_id='test_id')

        self.cm.circuitOpened(circuit)

        self.assertEqual(self.cm._open_circuit_map['test_id'], circuit)
        self.assertTrue(self.cm._sent_open_message)
        self.mock_logging.debug.assert_called_once_with(
            'Circuit manager notified that circuit test_id opened.')

        self.mock_assign_possible_pending_requests.assert_called_once_with(
            circuit)

        self.mock_logging.info.assert_called_once_with(
            'Circuit built successfully! oppy is ready to forward traffic :)')
