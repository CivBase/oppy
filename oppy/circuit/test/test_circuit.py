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
        self.circuit.path = Mock()

        self.mock_can_exit_to = patch_object(
            self.circuit.path.exit.exit_policy, 'can_exit_to').start()

    def test_buffering(self):
        self.circuit._state = 2

        result = self.circuit.canHandleRequest(Mock())

        self.assertFalse(result)
        self.assertFalse(self.mock_can_exit_to.called)

    def test_host_pending(self):
        self.circuit._state = 0

        result = self.circuit.canHandleRequest(Mock(is_host=True))

        self.assertTrue(result)
        self.assertFalse(self.mock_can_exit_to.called)

    def test_host(self):
        self.circuit._state = 1
        request = Mock(is_host=True)

        result = self.circuit.canHandleRequest(request)

        self.assertEqual(result, self.mock_can_exit_to.return_value)
        self.mock_can_exit_to.assert_called_once_with(
            port=request.port, strict=True)

    def test_ipv6_request_and_ipv6_ctype_pending(self):
        self.circuit._state = 0
        self.circuit.ctype = 1
        request = Mock(is_host=False, is_ipv6=True)

        result = self.circuit.canHandleRequest(request)

        self.assertTrue(result)
        self.assertFalse(self.mock_can_exit_to.called)

    def test_ipv6_request_and_ipv6_ctype(self):
        self.circuit._state = 1
        self.circuit.ctype = 1
        request = Mock(is_host=False, is_ipv6=True)

        result = self.circuit.canHandleRequest(request)

        self.assertTrue(result)
        self.mock_can_exit_to.assert_called_once_with(
            address=request.addr, port=request.port)

    def test_ipv4_request_and_ipv4_ctype_pending(self):
        self.circuit._state = 0
        self.circuit.ctype = 0
        request = Mock(is_host=False, is_ipv6=False, is_ipv4=True)

        result = self.circuit.canHandleRequest(request)

        self.assertTrue(result)
        self.assertFalse(self.mock_can_exit_to.called)

    def test_ipv4_request_and_ipv4_ctype(self):
        self.circuit._state = 1
        self.circuit.ctype = 0
        request = Mock(is_host=False, is_ipv6=False, is_ipv4=True)

        result = self.circuit.canHandleRequest(request)

        self.assertTrue(result)
        self.mock_can_exit_to.assert_called_once_with(
            address=request.addr, port=request.port)

    def test_ipv6_request_and_ipv4_ctype(self):
        self.circuit._state = 1
        self.circuit.ctype = 0
        request = Mock(is_host=False, is_ipv6=True, is_ipv4=False)

        result = self.circuit.canHandleRequest(request)

        self.assertFalse(result)
        self.assertFalse(self.mock_can_exit_to.called)

    def test_ipv4_request_and_ipv6_ctype(self):
        self.circuit._state = 1
        self.circuit.ctype = 1
        request = Mock(is_host=False, is_ipv6=False, is_ipv4=True)

        result = self.circuit.canHandleRequest(request)

        self.assertFalse(result)
        self.assertFalse(self.mock_can_exit_to.called)
