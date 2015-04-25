from mock import Mock

from oppy.circuit import circuit
from oppy.circuit.circuit import Circuit
from test.utils import BaseTestCase, patch_object


class CircuitCanHandleRequestTestCase(BaseTestCase):
    def setUp(self):
        super(CircuitCanHandleRequestTestCase, self).setUp()
        self.mock_selector = patch_object(circuit, 'PathSelector').start()
        self.mock_deferred_queue = patch_object(
            circuit.defer, 'DeferredQueue').start()

        self.mock_start_building = patch_object(
            Circuit, '_startBuilding').start()

        self.circuit = Circuit(1, Mock())

        self.mock_can_exit_to = patch_object(
            self.circuit.path.exit.exit_policy, 'can_exit_to').start()
