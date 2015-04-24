from mock import call, Mock, patch

from oppy.cell import cell, fixedlen, relay, varlen
from oppy.cell.cell import Cell as AbstractCell
from test.utils import BaseTestCase, concrete, patch_object


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


class CellEnoughDataForCellTestCase(BaseTestCase):
    def setUp(self):
        super(CellEnoughDataForCellTestCase, self).setUp()
        self.mock_struct = patch_object(cell, 'struct').start()

    def test_data_shorter_than_header(self):
        result = AbstractCell.enoughDataForCell(
            self.gen_data(2), link_version=1)

        self.assertFalse(result)
        self.assertFalse(self.mock_struct.unpack.called)

    def test_fixed_length_command(self):
        self.mock_struct.unpack.return_value = (None, 0)

        result = AbstractCell.enoughDataForCell(
            self.gen_data(514), link_version=4)

        self.assertTrue(result)
        self.mock_struct.unpack.assert_called_once_with('!IB', 'abcde')

    def test_fixed_length_command_shorter_than_required(self):
        self.mock_struct.unpack.return_value = (None, 0)

        result = AbstractCell.enoughDataForCell(
            self.gen_data(509), link_version=4)

        self.assertFalse(result)
        self.mock_struct.unpack.assert_called_once_with('!IB', 'abcde')

    def test_variable_length_command(self):
        self.mock_struct.unpack.side_effect = [(None, 7), (8, None)]

        result = AbstractCell.enoughDataForCell(
            self.gen_data(8), link_version=4)

        self.assertTrue(result)
        self.mock_struct.unpack.assert_has_calls([
            call('!IB', 'abcde'),
            call('!H', 'fg')])

    def test_variable_length_command_shorter_than_required(self):
        self.mock_struct.unpack.side_effect = [(None, 7), (8, None)]

        result = AbstractCell.enoughDataForCell(
            self.gen_data(7), link_version=4)

        self.assertFalse(result)
        self.mock_struct.unpack.assert_has_calls([
            call('!IB', 'abcde'),
            call('!H', 'fg')])

    def test_error_invalid_command(self):
        self.mock_struct.unpack.return_value = (None, 'not a real command')

        self.assertRaisesRegexp(
            cell.UnknownCellCommand,
            '^Unknown cell cmd: not a real command.$',
            AbstractCell.enoughDataForCell,
            self.gen_data(5),
            link_version=4)

        self.mock_struct.unpack.assert_called_once_with('!IB', 'abcde')


class CellParseTestCase(BaseTestCase):
    def setUp(self):
        super(CellParseTestCase, self).setUp()
        self.mock_struct = patch_object(cell, 'struct').start()

        self.mock_struct.calcsize.return_value = 5

    @patch_object(varlen, 'VarLenCell')
    def test_varlen(self, mock_varlencell):
        self.mock_struct.unpack.return_value = ('circ id', 7)

        result = AbstractCell.parse(self.gen_data(6), link_version=4)

        self.assertEqual(result, mock_varlencell._parse.return_value)
        self.mock_struct.calcsize.assert_called_once_with('!IB')
        self.mock_struct.unpack.assert_called_once_with('!IB', 'abcde')
        mock_varlencell.Header.assert_called_once_with(
            circ_id='circ id', cmd=7, link_version=4)

        mock_varlencell._parse.assert_called_once_with(
            'abcdef', mock_varlencell.Header.return_value)

    @patch_object(relay, 'RelayCell')
    def test_relay(self, mock_relaycell):
        self.mock_struct.unpack.return_value = ('circ id', 3)

        result = AbstractCell.parse(self.gen_data(6), link_version=4)

        self.assertEqual(result, mock_relaycell._parse.return_value)
        self.mock_struct.calcsize.assert_called_once_with('!IB')
        self.mock_struct.unpack.assert_called_once_with('!IB', 'abcde')
        mock_relaycell.Header.assert_called_once_with(
            circ_id='circ id', cmd=3, link_version=4)

        mock_relaycell._parse.assert_called_once_with(
            'abcdef', mock_relaycell.Header.return_value)

    @patch_object(fixedlen, 'FixedLenCell')
    def test_relay_encrypted(self, mock_fixedlencell):
        self.mock_struct.unpack.return_value = ('circ id', 3)

        result = AbstractCell.parse(
            self.gen_data(6), link_version=4, encrypted=True)

        self.assertEqual(result, mock_fixedlencell._parse.return_value)
        self.mock_struct.calcsize.assert_called_once_with('!IB')
        self.mock_struct.unpack.assert_called_once_with('!IB', 'abcde')
        mock_fixedlencell.Header.assert_called_once_with(
            circ_id='circ id', cmd=3, link_version=4)

        mock_fixedlencell._parse.assert_called_once_with(
            'abcdef', mock_fixedlencell.Header.return_value)

    @patch_object(fixedlen, 'FixedLenCell')
    def test_fixedlen(self, mock_fixedlencell):
        self.mock_struct.unpack.return_value = ('circ id', 0)

        result = AbstractCell.parse(self.gen_data(6), link_version=4)

        self.assertEqual(result, mock_fixedlencell._parse.return_value)
        self.mock_struct.calcsize.assert_called_once_with('!IB')
        self.mock_struct.unpack.assert_called_once_with('!IB', 'abcde')
        mock_fixedlencell.Header.assert_called_once_with(
            circ_id='circ id', cmd=0, link_version=4)

        mock_fixedlencell._parse.assert_called_once_with(
            'abcdef', mock_fixedlencell.Header.return_value)

    def test_error_invalid_link_version_low(self):
        self.assertRaisesRegexp(
            ValueError,
            '^link_version must be leq 4, but found 0 instead$',
            AbstractCell.parse,
            None,
            link_version=0)

        self.assertFalse(self.mock_struct.calcsize.called)
        self.assertFalse(self.mock_struct.unpack.called)

    def test_error_invalid_link_version_high(self):
        self.assertRaisesRegexp(
            ValueError,
            '^link_version must be leq 4, but found 5 instead$',
            AbstractCell.parse,
            None,
            link_version=5)

        self.assertFalse(self.mock_struct.calcsize.called)
        self.assertFalse(self.mock_struct.unpack.called)

    def test_error_data_shorter_than_header(self):
        self.assertRaises(
            cell.NotEnoughBytes,
            AbstractCell.parse,
            self.gen_data(4),
            link_version=1)

        self.mock_struct.calcsize.assert_called_once_with('!HB')
        self.assertFalse(self.mock_struct.unpack.called)

    def test_error_invalid_command(self):
        self.mock_struct.unpack.return_value = (None, 'not a real command')

        self.assertRaisesRegexp(
            cell.UnknownCellCommand,
            '^When parsing cell data, found an unknown cmd: not a real '
            'command.$',
            AbstractCell.parse,
            self.gen_data(5),
            link_version=4)

        self.mock_struct.calcsize.assert_called_once_with('!IB')
        self.mock_struct.unpack.assert_called_once_with('!IB', 'abcde')


class CellParseHelperTestCase(BaseTestCase):
    def setUp(self):
        super(CellParseHelperTestCase, self).setUp()
        self.mock_get_subclass = patch.object(
            AbstractCell, '_getSubclass').start()

        self.mock_cell = (
            self.mock_get_subclass.return_value.return_value)

    def test_parse_helper(self):
        self.mock_cell.__len__.return_value = 5
        header = Mock(
            spec=AbstractCell.Header, cmd='command', link_version=4)

        result = AbstractCell._parse(self.gen_data(5), header)

        self.assertEqual(result, self.mock_cell)
        self.mock_get_subclass.assert_called_once_with(header, 'abcde')
        self.mock_get_subclass.return_value.assert_called_once_with(header)
        self.mock_cell._parseHeader.assert_called_once_with('abcde')
        self.mock_cell._parsePayload.assert_called_once_with('abcde')

    def test_error_invalid_header(self):
        self.assertRaisesRegexp(
            TypeError,
            '^The given header object has the wrong type.$',
            AbstractCell._parse,
            None,
            None)

        self.assertFalse(self.mock_get_subclass.called)

    def test_error_invalid_header_command(self):
        header = Mock(spec=AbstractCell.Header, cmd=None, link_version=4)

        self.assertRaisesRegexp(
            ValueError,
            '^Fields of the given header object are invalid.$',
            AbstractCell._parse,
            None,
            header)

        self.assertFalse(self.mock_get_subclass.called)

    def test_error_invalid_header_link_version(self):
        header = Mock(
            spec=AbstractCell.Header, cmd='command', link_version=None)

        self.assertRaisesRegexp(
            ValueError,
            '^Fields of the given header object are invalid.$',
            AbstractCell._parse,
            None,
            header)

        self.assertFalse(self.mock_get_subclass.called)

    def test_error_short_data(self):
        self.mock_cell.__len__.return_value = 5
        header = Mock(
            spec=AbstractCell.Header, cmd='command', link_version=4)

        self.assertRaisesRegexp(
            cell.NotEnoughBytes,
            '^Needed 5 bytes to finish parsing data; only found 4.$',
            AbstractCell._parse,
            self.gen_data(4),
            header)

        self.mock_get_subclass.assert_called_once_with(header, 'abcd')
        self.mock_get_subclass.return_value.assert_called_once_with(header)
        self.mock_cell._parseHeader.assert_called_once_with('abcd')
        self.assertFalse(self.mock_cell._parsePayload.called)


class CellRepresentTestCase(BaseTestCase):
    def setUp(self):
        super(CellRepresentTestCase, self).setUp()
        self.cell = Cell()

    def test_represent(self):
        self.cell.header = 'header'
        self.cell.payload = 'payload'

        result = repr(self.cell)

        self.assertEqual(
            result, "concrete_Cell(header=header, payload='payload')")


class CellLengthTestCase(BaseTestCase):
    def setUp(self):
        super(CellLengthTestCase, self).setUp()
        self.mock_cell_payload_range = Mock()

        self.cell = Cell()
        self.cell.payloadRange = self.mock_cell_payload_range

        self.mock_cell_payload_range.return_value = [1, 2]

    def test_length(self):
        result = len(self.cell)

        self.assertEqual(result, 2)


class CellEqualTestCase(BaseTestCase):
    def setUp(self):
        super(CellEqualTestCase, self).setUp()
        self.cell = Cell()

    def test_equal(self):
        self.assertTrue(self.cell == Cell())

    def test_not_equal_dicts(self):
        expected = Cell()
        expected.header = 'header'

        self.assertFalse(self.cell == expected)

    def test_not_equal_types(self):
        self.assertFalse(self.cell == 'cell')
