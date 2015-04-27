from oppy.util import exitrequest
from oppy.util.exitrequest import ExitRequest
from test.utils import BaseTestCase, patch_object


class ExitRequestInitTestCase(BaseTestCase):
    def setUp(self):
        super(ExitRequestInitTestCase, self).setUp()
        self.mock_unpack = patch_object(exitrequest.struct, 'unpack').start()
        self.mock_ip_address = patch_object(
            exitrequest.ipaddress, 'ip_address').start()
