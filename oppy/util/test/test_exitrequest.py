from mock import Mock

from oppy.util import exitrequest
from oppy.util.exitrequest import ExitRequest
from test.utils import BaseTestCase, patch_object


class ExitRequestInitTestCase(BaseTestCase):
    def setUp(self):
        super(ExitRequestInitTestCase, self).setUp()
        self.mock_unpack = patch_object(exitrequest.struct, 'unpack').start()
        self.mock_ip_address = patch_object(
            exitrequest.ipaddress, 'ip_address').start()

        self.mock_unpack.return_value = ['port']

    def test_no_addr(self):
        self.mock_unpack.return_value = ['port']
        port = Mock()
        host = Mock()

        result = ExitRequest(port, host=host)

        self.assertEqual(result.port, 'port')
        self.assertIsNone(result.addr)
        self.assertEqual(result.host, host)
        self.assertFalse(result.is_ipv4)
        self.assertFalse(result.is_ipv6)
        self.assertTrue(result.is_host)
        self.mock_unpack.assert_called_once_with('!H', port)
        self.assertFalse(self.mock_ip_address.called)

    def test_ipv4_addr(self):
        ip_addr = Mock(spec=exitrequest.ipaddress.IPv4Address)
        self.mock_ip_address.return_value = ip_addr
        port = Mock()
        addr = Mock()

        result = ExitRequest(port, addr=addr)

        self.assertEqual(result.port, 'port')
        self.assertEqual(result.addr, bytes(ip_addr.exploded))
        self.assertIsNone(result.host)
        self.assertTrue(result.is_ipv4)
        self.assertFalse(result.is_ipv6)
        self.assertFalse(result.is_host)
        self.mock_unpack.assert_called_once_with('!H', port)
        self.mock_ip_address.assert_called_once_with(addr)

    def test_ipv6_addr(self):
        ip_addr = Mock(spec=exitrequest.ipaddress.IPv6Address)
        self.mock_ip_address.return_value = ip_addr
        port = Mock()
        addr = Mock()

        result = ExitRequest(port, addr=addr)

        self.assertEqual(result.port, 'port')
        self.assertEqual(result.addr, bytes(ip_addr.exploded))
        self.assertIsNone(result.host)
        self.assertFalse(result.is_ipv4)
        self.assertTrue(result.is_ipv6)
        self.assertFalse(result.is_host)
        self.mock_unpack.assert_called_once_with('!H', port)
        self.mock_ip_address.assert_called_once_with(addr)

    def test_error_no_addr_or_host(self):
        port = Mock()

        self.assertRaises(
            AssertionError,
            ExitRequest,
            port)

        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_ip_address.called)

    def test_error_addr_and_host(self):
        port = Mock()
        addr = Mock()
        host = Mock()

        self.assertRaises(
            AssertionError,
            ExitRequest,
            port,
            addr=addr,
            host=host)

        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_ip_address.called)
