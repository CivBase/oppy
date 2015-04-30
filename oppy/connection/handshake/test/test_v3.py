from mock import call, Mock, patch
patch('oppy.util.tools.dispatch', lambda d, k: lambda f: f).start()
patch('oppy.connection.handshake.v3.dispatch', lambda d, k: lambda f: f).start()

from oppy.connection.handshake import v3
from oppy.connection.handshake.v3 import V3FSM
from test.utils import BaseTestCase, patch_object


class V3FSMProcessVersionsTestCase(BaseTestCase):
    def setUp(self):
        super(V3FSMProcessVersionsTestCase, self).setUp()
        self.transport = Mock()
        self.v3fsm = V3FSM(self.transport)

        self.mock_verify_cell_cmd = patch.object(
            V3FSM, '_verifyCellCmd').start()

        self.mock_handshake_supported = patch_object(
            self.v3fsm, 'handshakeSupported').start()

    def test_process_versions(self):
        cell = Mock(header=Mock(cmd=Mock()), versions=[3])

        result = self.v3fsm._response_map[1](self.v3fsm, cell)

        self.assertIsNone(result)
        self.assertEqual(self.v3fsm._state, 2)
        self.mock_verify_cell_cmd.assert_called_once_with(cell.header.cmd, 7)
        self.mock_handshake_supported.assert_called_once_with()

    def test_error_unsupported_versions(self):
        cell = Mock(header=Mock(cmd=Mock()), versions=[])

        self.assertRaisesRegexp(
            v3.HandshakeFailed,
            '^Relay does not support Link Protocol 3$',
            self.v3fsm._response_map[1],
            self.v3fsm,
            cell)

        self.mock_verify_cell_cmd.assert_called_once_with(cell.header.cmd, 7)
        self.assertFalse(self.mock_handshake_supported.called)

    def test_error_unsupported_handshake(self):
        self.mock_handshake_supported.return_value = False
        cell = Mock(header=Mock(cmd=Mock()), versions=[3])

        self.assertRaisesRegexp(
            v3.HandshakeFailed,
            '^Relay does not support Link Protocol 3$',
            self.v3fsm._response_map[1],
            self.v3fsm,
            cell)

        self.mock_verify_cell_cmd.assert_called_once_with(cell.header.cmd, 7)
        self.mock_handshake_supported.assert_called_once_with()


class V3FSMProcessCertsHelperTestCase(BaseTestCase):
    def setUp(self):
        super(V3FSMProcessCertsHelperTestCase, self).setUp()
        self.transport = Mock()
        self.v3fsm = V3FSM(self.transport)

        self.mock_verify_cell_cmd = patch.object(
            V3FSM, '_verifyCellCmd').start()

        self.mock_der_cert_to_pem_cert = patch_object(
            v3.ssl, 'DER_cert_to_PEM_cert').start()

        self.mock_load_certificate = patch_object(
            v3.SSLCrypto, 'load_certificate').start()

        self.mock_get_peer_certificate = patch_object(
            self.transport, 'getPeerCertificate').start()

        self.mock_valid_cert_time = patch_object(
            v3.crypto_util, 'validCertTime').start()

        self.mock_dump_privatekey = patch_object(
            v3.SSLCrypto, 'dump_privatekey').start()

        self.mock_verify_cert_sig = patch_object(
            v3.crypto_util, 'verifyCertSig').start()

        self.mock_link_cert = Mock()
        self.mock_id_cert = Mock()
        self.mock_load_certificate.side_effect = iter([
            self.mock_link_cert, self.mock_id_cert])

        self.mock_conn_cert = self.mock_get_peer_certificate.return_value
        self.mock_id_key = self.mock_id_cert.get_pubkey.return_value
        self.mock_id_key.type.return_value = 6
        self.mock_id_key.bits.return_value = 1024
        self.mock_verify_cert_sig.return_value = True

    def test_process_certs(self):
        mock_link_asn1_key = mock_conn_asn1_key = Mock()
        self.mock_dump_privatekey.side_effect = iter([
            mock_link_asn1_key, mock_conn_asn1_key])

        cell = Mock(num_certs=2, cert_payload_items=[
            Mock(cert_type=1, cert='cert1'),
            Mock(cert_type=2, cert='cert2')])

        result = self.v3fsm._response_map[2](self.v3fsm, cell)

        self.assertIsNone(result)
        self.assertEqual(self.v3fsm._state, 3)
        self.mock_verify_cell_cmd.assert_called_once_with(cell.header.cmd, 129)
        self.mock_der_cert_to_pem_cert.assert_has_calls([
            call('cert1'), call('cert2')])

        self.mock_load_certificate.assert_has_calls([
            call(1, self.mock_der_cert_to_pem_cert.return_value),
            call(1, self.mock_der_cert_to_pem_cert.return_value)])

        self.mock_get_peer_certificate.assert_called_once_with()
        self.mock_id_cert.get_pubkey.assert_called_once_with()
        self.mock_link_cert.get_pubkey.assert_called_once_with()
        self.mock_conn_cert.get_pubkey.assert_called_once_with()
        self.mock_valid_cert_time.assert_has_calls([
            call(self.mock_link_cert), call(self.mock_id_cert)])

        self.mock_dump_privatekey.assert_has_calls([
            call(2, self.mock_link_cert.get_pubkey.return_value),
            call(2, self.mock_conn_cert.get_pubkey.return_value)])

        self.mock_id_key.type.assert_called_once_with()

    def test_error_unexpected_certs(self):
        mock_link_asn1_key = mock_conn_asn1_key = Mock()
        self.mock_dump_privatekey.side_effect = iter([
            mock_link_asn1_key, mock_conn_asn1_key])

        cell = Mock(num_certs=2, cert_payload_items=[
            Mock(cert_type=3, cert='cert3'),
            Mock(cert_type=4, cert='cert4')])

        self.assertRaisesRegexp(
            v3.HandshakeFailed,
            '^Unexpected certificate type in Certs cell: 3$',
            self.v3fsm._response_map[2],
            self.v3fsm,
            cell)

        self.mock_verify_cell_cmd.assert_called_once_with(cell.header.cmd, 129)
        self.assertFalse(self.mock_der_cert_to_pem_cert.called)
        self.assertFalse(self.mock_load_certificate.called)
        self.assertFalse(self.mock_get_peer_certificate.called)
        self.assertFalse(self.mock_id_cert.get_pubkey.called)
        self.assertFalse(self.mock_link_cert.get_pubkey.called)
        self.assertFalse(self.mock_conn_cert.get_pubkey.called)
        self.assertFalse(self.mock_valid_cert_time.called)
        self.assertFalse(self.mock_dump_privatekey.called)
        self.assertFalse(self.mock_id_key.type.called)
