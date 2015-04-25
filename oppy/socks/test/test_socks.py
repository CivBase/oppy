from oppy.socks import socks
from oppy.socks.socks import OppySOCKSProtocol
from test.utils import BaseTestCase, patch_object


class OppySOCKSProtocolHandleRequestHelperTestCase(BaseTestCase):
    def setUp(self):
        super(OppySOCKSProtocolHandleRequestHelperTestCase, self).setUp()
        self.protocol = OppySOCKSProtocol()

        self.mock_send_reply = patch_object(self.protocol, '_sendReply').start()
        self.mock_lose_connection = patch_object(
            self.protocol.transport, 'loseConnection').start()

        self.mock_exit_request = patch_object(socks, 'ExitRequest').start()
        self.mock_stream = patch_object(socks, 'Stream').start()
