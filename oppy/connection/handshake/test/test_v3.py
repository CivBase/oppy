from mock import call, Mock, patch
patch('oppy.util.tools.dispatch', lambda d, k: lambda f: f).start()
patch('oppy.connection.handshake.v3.dispatch', lambda d, k: lambda f: f).start()

from oppy.connection.handshake import v3
from oppy.connection.handshake.v3 import V3FSM
from test.utils import BaseTestCase, patch_object


class V3FSMProcessCertsHelperTestCase(BaseTestCase):
    def setUp(self):
        super(V3FSMProcessCertsHelperTestCase, self).setUp()
        self.transport = Mock()
        self.v3fsm = V3FSM(self.transport)

        self.mock_verify_cell_cmd = patch_object(
            self.v3fsm, '_verifyCellCmd').start()

        self.mock_der_cert_to_pem_cert = patch_object(
            v3.ssl, 'DER_cert_to_PEM_cert').start()

        self.mock_load_certificate = patch_object(
            v3.SSLCrypto, 'load_certificate').start()

        self.mock_get_peer_certificate = patch_object(
            self.transport, 'getPeerCertificate').start()

        self.mock_dump_privatekey = patch_object(
            v3.SSLCrypto, 'dump_privatekey').start()

        self.mock_link_cert = Mock()
        self.mock_id_cert = Mock()
        self.mock_load_certificate.side_effect = [
            self.mock_link_cert, self.mock_id_cert]

        self.mock_conn_cert = self.mock_get_peer_certificate.return_value
        self.mock_link_asn1_key = Mock()
        self.mock_conn_asn1_key = Mock()
        self.mock_dump_privatekey.side_effect = [
            self.mock_link_asn1_key, self.mock_conn_asn1_key]

    # def test_process_certs(self):
    #     cell = Mock(num_certs=1, cert_payload_items=[
    #         Mock(cert_type=1, cert='cert1'),
    #         Mock(cert_type=2, cert='cert2')])
    #
    #     result = self.v3fsm._processCerts(cell)
    #
    #     self.assertIsNone(result)
    #     self.assertEqual(self.v3fsm._state, 3)
    #     self.mock_verify_cell_cmd.assert_called_once_with(cell.header.cmd, 129)
    #     self.mock_der_cert_to_pem_cert.assert_has_calls([
    #         call('cert1'), call('cert2')])
    #
    #     self.mock_load_certificate.assert_has_calls([
    #         call(0, self.mock_der_cert_to_pem_cert.return_value),
    #         call(1, self.mock_der_cert_to_pem_cert.return_value)])
    #
    #     self.mock_get_peer_certificate.assert_called_once_with()
    #     self.mock_id_cert.get_pubkey.assert_called_once_with()
    #     self.mock_link_cert.get_pubkey.assert_called_once_with()
    #     self.mock_conn_cert.get_pubkey.assert_called_once_with()
    #     self.mock_dump_privatekey.assert_has_calls([
    #         call(0, self.mock_link_cert.get_pubkey.return_value),
    #         call(0, self.mock_conn_cert.get_pubkey.return_value)])
