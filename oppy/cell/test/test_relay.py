from oppy.cell import relay
from oppy.cell.relay import RelayExtend2Cell
from test.utils import BaseTestCase, patch_object


class RelayExtend2CellMakeTestCase(BaseTestCase):
    def setUp(self):
        super(RelayExtend2CellMakeTestCase, self).setUp()
        self.mock_fixedlen_header = patch_object(
            relay.FixedLenCell, 'Header').start()

        self.mock_relay_header = patch_object(
            relay.RelayCell, 'RelayHeader').start()

        self.mock_relay_extend_2_cell = patch_object(
            relay, 'RelayExtend2Cell').start()

    def test_make(self):
        hdata = self.gen_data(84)

        result = RelayExtend2Cell.make(
            1, hdata=hdata, lspecs=[self.gen_data(8)])

        self.assertEqual(result, self.mock_relay_extend_2_cell.return_value)
        self.mock_fixedlen_header.assert_called_once_with(
            circ_id=1, cmd=9, link_version=3)

        self.mock_relay_header.assert_called_once_with(
            cmd=14, recognized="\x00\x00", stream_id=0,
            digest="\x00\x00\x00\x00", rpayload_len=97)

        self.mock_relay_extend_2_cell.assert_called_once_with(
            self.mock_fixedlen_header.return_value,
            rheader=self.mock_relay_header.return_value, nspec=1,
            lspecs=['abcdefgh'], htype=2, hlen=84, hdata=hdata)
