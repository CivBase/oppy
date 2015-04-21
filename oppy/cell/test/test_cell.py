from mock import Mock

from oppy.cell.cell import Cell as AbstractCell
from test.utils import BaseTestCase, concrete


Cell = concrete(AbstractCell)


class CellGetPayloadTestCase(BaseTestCase):
    def setUp(self):
        super(CellGetPayloadTestCase, self).setUp()
        self.mock_cell_payload_range = Mock()
        self.mock_cell_get_bytes = Mock()

        self.cell = Cell()
        self.cell.payloadRange = self.mock_cell_payload_range
        self.cell.getBytes = self.mock_cell_get_bytes

        self.mock_cell_payload_range.return_value = [1, 2]
        self.mock_cell_get_bytes.return_value = [1, 2, 3]

    def test_get_payload(self):
        result = self.cell.getPayload()

        self.assertItemsEqual(result, [2, 3])
