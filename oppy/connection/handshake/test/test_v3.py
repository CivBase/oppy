from mock import Mock

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
