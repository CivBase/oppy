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
        lspecs = [self.gen_data(8), self.gen_data(20)]

        result = RelayExtend2Cell.make(1, hdata=hdata, lspecs=lspecs, early=False)

        self.assertEqual(result, self.mock_relay_extend_2_cell.return_value)
        self.mock_fixedlen_header.assert_called_once_with(circ_id=1, cmd=3, link_version=3)
        self.mock_relay_header.assert_called_once_with(
            cmd=14, recognized="\x00\x00", stream_id=0,
            digest="\x00\x00\x00\x00", rpayload_len=117)

        self.mock_relay_extend_2_cell.assert_called_once_with(
            self.mock_fixedlen_header.return_value,
            rheader=self.mock_relay_header.return_value, nspec=2,
            lspecs=lspecs, htype=2, hlen=84, hdata=hdata)

    def test_lspecs_none(self):
        hdata = self.gen_data(84)

        self.assertRaisesRegexp(
            relay.BadPayloadData,
            '^No Link Specifiers found. At least 1 Link Specifier is required.$',
            RelayExtend2Cell.make,
            1,
            hdata=hdata)

        self.mock_fixedlen_header.assert_called_once_with(circ_id=1, cmd=9, link_version=3)
        self.assertFalse(self.mock_relay_header.called)
        self.assertFalse(self.mock_relay_extend_2_cell.called)

    def test_lspecs_none_stream_id_not_zero(self):
        hdata = self.gen_data(84)

        self.assertRaisesRegexp(
            relay.BadPayloadData,
            '^EXTEND2 cells should use stream_id=0.$',
            RelayExtend2Cell.make,
            1,
            stream_id=1,
            hdata=hdata)

        self.assertFalse(self.mock_fixedlen_header.called)
        self.assertFalse(self.mock_relay_header.called)
        self.assertFalse(self.mock_relay_extend_2_cell.called)

    def test_stream_id_not_zero(self):
        hdata = self.gen_data(84)
        lspecs = [self.gen_data(8), self.gen_data(20)]

        self.assertRaisesRegexp(
            relay.BadPayloadData,
            '^EXTEND2 cells should use stream_id=0.$',
            RelayExtend2Cell.make,
            1,
            stream_id=1,
            lspecs=lspecs,
            hdata=hdata)

        self.assertFalse(self.mock_fixedlen_header.called)
        self.assertFalse(self.mock_relay_header.called)
        self.assertFalse(self.mock_relay_extend_2_cell.called)

    def test_htype_not_ntor_handshake(self):
        hdata = self.gen_data(84)
        lspecs = [self.gen_data(8), self.gen_data(20)]

        self.assertRaisesRegexp(
            relay.BadPayloadData,
            '^htype was 1, but we currently only support 2 \(NTor\) handshakes.$',
            RelayExtend2Cell.make,
            1,
            lspecs=lspecs,
            htype=1,
            hdata=hdata)

        self.assertFalse(self.mock_fixedlen_header.called)
        self.assertFalse(self.mock_relay_header.called)
        self.assertFalse(self.mock_relay_extend_2_cell.called)

    def test_hlen_not_ntor_hlen(self):
        hdata = self.gen_data(84)
        lspecs = [self.gen_data(8), self.gen_data(20)]

        self.assertRaisesRegexp(
            relay.BadPayloadData,
            '^htype was NTor and hlen was 83 but expecting 84$',
            RelayExtend2Cell.make,
            1,
            lspecs=lspecs,
            hlen=83,
            hdata=hdata)

        self.assertFalse(self.mock_fixedlen_header.called)
        self.assertFalse(self.mock_relay_header.called)
        self.assertFalse(self.mock_relay_extend_2_cell.called)

    def test_hlen_not_len_of_hdata(self):
        hdata = self.gen_data(83)
        lspecs = [self.gen_data(8), self.gen_data(20)]

        self.assertRaisesRegexp(
            relay.BadPayloadData,
            '^hlen 84 neq len\(hdata\) 83$',
            RelayExtend2Cell.make,
            1,
            lspecs=lspecs,
            hdata=hdata)

        self.assertFalse(self.mock_fixedlen_header.called)
        self.assertFalse(self.mock_relay_header.called)
        self.assertFalse(self.mock_relay_extend_2_cell.called)