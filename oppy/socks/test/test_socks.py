from mock import Mock

from oppy.socks import socks
from oppy.socks.socks import OppySOCKSProtocol
from test.utils import BaseTestCase, patch_object


class OppySOCKSProtocolHandleRequestHelperTestCase(BaseTestCase):
    def data(self, addr_type, ver=False, connect=False, rsv=False):
        addr_types = {
            'ipv4': '\x01',
            'domain name': '\x03',
            'ipv6': '\x04',
            'unsupported': 'unsupported'
        }

        end_data = {
            'ipv4': ['a'] * 4 + ['b'] * 2,
            'domain name': ['c'] + ['d'] * 5 + ['e'] * 2,
            'ipv6': ['f'] * 16 + ['g'] * 2,
            'unsupported': []
        }

        data_arr = [
            '\x05' if ver else 'ver',
            '\x01' if connect else 'connect',
            '\x00' if rsv else 'rsv',
            addr_types[addr_type]] + end_data[addr_type]

        # creating a custom getitem operator is easier than creating a new
        # bytestring from scratch (overloading array[slice])
        data = Mock()
        data.__getitem__ = lambda s, val: (
            ''.join(data_arr[val.start:val.stop]) if isinstance(val, slice)
            else data_arr[val])

        return data

    def setUp(self):
        super(OppySOCKSProtocolHandleRequestHelperTestCase, self).setUp()
        self.protocol = OppySOCKSProtocol()
        self.protocol.transport = Mock()

        self.mock_logging = patch_object(socks, 'logging').start()
        self.mock_send_reply = patch_object(self.protocol, '_sendReply').start()
        self.mock_lose_connection = patch_object(
            self.protocol.transport, 'loseConnection').start()

        self.mock_exit_request = patch_object(socks, 'ExitRequest').start()
        self.mock_unpack = patch_object(socks.struct, 'unpack').start()
        self.mock_stream = patch_object(socks, 'Stream').start()

        self.mock_unpack.return_value = [5]
        self.request = Mock()
        self.protocol.request = self.request

    def test_ipv4_ver_connect_rsv(self):
        data = self.data('ipv4', ver=True, connect=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 2)
        self.assertEqual(
            self.protocol.request, self.mock_exit_request.return_value)

        self.assertFalse(self.mock_logging.error.called)
        self.assertFalse(self.mock_lose_connection.called)
        self.assertFalse(self.mock_unpack.called)
        self.mock_exit_request.assert_called_once_with('bb', addr='aaaa')
        self.mock_stream.assert_called_once_with(
            self.protocol.request, self.protocol)

        self.mock_send_reply.assert_called_once_with('\x00')

    def test_ipv4_connect_rsv(self):
        data = self.data('ipv4', connect=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'Unsupported SOCKS version: ver.')

        self.mock_send_reply.assert_called_once_with('\x01')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_ipv4_ver_rsv(self):
        data = self.data('ipv4', ver=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'SOCKS client tried an unsupported request: connect.')

        self.mock_send_reply.assert_called_once_with('\x07')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_ipv4(self):
        data = self.data('ipv4')
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'Unsupported SOCKS version: ver.')

        self.mock_send_reply.assert_called_once_with('\x01')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_domain_name_ver_connect(self):
        data = self.data('domain name', ver=True, connect=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'Reserved byte was non-zero in SOCKS client request.')

        self.mock_send_reply.assert_called_once_with('\x01')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_domain_name_rsv(self):
        data = self.data('domain name', rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'Unsupported SOCKS version: ver.')

        self.mock_send_reply.assert_called_once_with('\x01')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_domain_name_ver_connect_rsv(self):
        data = self.data('domain name', ver=True, connect=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 2)
        self.assertEqual(
            self.protocol.request, self.mock_exit_request.return_value)

        self.assertFalse(self.mock_logging.error.called)
        self.assertFalse(self.mock_lose_connection.called)
        self.mock_unpack.assert_called_once_with('!B', 'c')
        self.mock_exit_request.assert_called_once_with('ee', host='ddddd')
        self.mock_stream.assert_called_once_with(
            self.protocol.request, self.protocol)

        self.mock_send_reply.assert_called_once_with('\x00')

    def test_ipv6_ver_connect_rsv(self):
        data = self.data('ipv6', ver=True, connect=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 2)
        self.assertEqual(
            self.protocol.request, self.mock_exit_request.return_value)

        self.assertFalse(self.mock_logging.error.called)
        self.assertFalse(self.mock_lose_connection.called)
        self.assertFalse(self.mock_unpack.called)
        self.mock_exit_request.assert_called_once_with('gg', addr='f' * 16)
        self.mock_stream.assert_called_once_with(
            self.protocol.request, self.protocol)

        self.mock_send_reply.assert_called_once_with('\x00')

    def test_ipv6_connect_rsv(self):
        data = self.data('ipv6', connect=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'Unsupported SOCKS version: ver.')

        self.mock_send_reply.assert_called_once_with('\x01')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_ipv6_ver_rsv(self):
        data = self.data('ipv6', ver=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'SOCKS client tried an unsupported request: connect.')

        self.mock_send_reply.assert_called_once_with('\x07')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_ipv6_ver_connect(self):
        data = self.data('ipv6', ver=True, connect=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'Reserved byte was non-zero in SOCKS client request.')

        self.mock_send_reply.assert_called_once_with('\x01')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_unsupported_ver_connect_rsv(self):
        data = self.data('unsupported', ver=True, connect=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.assertFalse(self.mock_logging.error.called)
        self.mock_send_reply.assert_called_once_with('\x08')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_unsupported_connect_rsv(self):
        data = self.data('unsupported', connect=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'Unsupported SOCKS version: ver.')

        self.mock_send_reply.assert_called_once_with('\x01')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_unsupported_ver_rsv(self):
        data = self.data('unsupported', ver=True, rsv=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'SOCKS client tried an unsupported request: connect.')

        self.mock_send_reply.assert_called_once_with('\x07')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)

    def test_unsupported_ver_connect(self):
        data = self.data('unsupported', ver=True, connect=True)
        self.protocol._handleRequest(data)

        self.assertEqual(self.protocol.state, 0)
        self.assertEqual(self.protocol.request, self.request)
        self.mock_logging.error.assert_called_once_with(
            'Reserved byte was non-zero in SOCKS client request.')

        self.mock_send_reply.assert_called_once_with('\x01')
        self.mock_lose_connection.assert_called_once_with()
        self.assertFalse(self.mock_unpack.called)
        self.assertFalse(self.mock_exit_request.called)
        self.assertFalse(self.mock_stream.called)
