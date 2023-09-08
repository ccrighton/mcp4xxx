# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.nz>
#
# SPDX-License-Identifier: MIT
import unittest
from unittest import mock
from unittest.mock import MagicMock
from unittest.mock import patch

wiper0 = 0
tcon_shutdown0 = False
terminal_a_status0 = True
wiper_status0 = True
terminal_b_status0 = True
wiper1 = 0
tcon_shutdown1 = False
terminal_a_status1 = True
wiper_status1 = True
terminal_b_status1 = True


def write_readinto(write_buf, read_buf):
    global wiper0, wiper1
    global tcon_shutdown0, tcon_shutdown1
    global terminal_a_status0, terminal_a_status1
    global wiper_status0, wiper_status1
    global terminal_b_status0, terminal_b_status1

    command_read = (write_buf[0] & 0b00001100) >> 2 == 0b11
    command_write = (write_buf[0] & 0b00001100) >> 2 == 0b00
    command_increment = (write_buf[0] & 0b00001100) >> 2 == 0b01
    command_decrement = (write_buf[0] & 0b00001100) >> 2 == 0b10
    address_wiper0 = (write_buf[0] & 0b11110000) >> 4 == 0b0000
    address_wiper1 = (write_buf[0] & 0b11110000) >> 4 == 0b0001
    address_tcon = (write_buf[0] & 0b11110000) >> 4 == 0b0100
    address_status = (write_buf[0] & 0b11110000) >> 4 == 0b0101
    if command_read and (address_wiper0 | address_wiper1):
        read_buf[0] = (write_buf[0] & 0b11111110)
        read_buf[0] = (read_buf[0]) | ((wiper0 if address_wiper0 else wiper1) & 0x1FF) >> 8
        read_buf[1] = (wiper0 if address_wiper0 else wiper1) & 0xFF
    elif command_write and (address_wiper0 | address_wiper1):
        read_buf[0] = write_buf[0] & 0b11111110
        value = write_buf[1] | ((write_buf[0] & 0b00000001) << 8)
        if value > 256:
            if address_wiper0:
                wiper0 = 256
            elif address_wiper1:
                wiper1 = 256
        else:
            if address_wiper0:
                wiper0 = value
            elif address_wiper1:
                wiper1 = value
        read_buf[1] = write_buf[1]
    elif command_increment and (address_wiper0 | address_wiper1):
        read_buf[0] = write_buf[0] & 0b11111110
        if address_wiper0:
            if wiper0 < 256:
                wiper0 += 1
        elif address_wiper1:
            if wiper1 < 256:
                wiper1 += 1
    elif command_decrement and (address_wiper0 | address_wiper1):
        read_buf[0] = write_buf[0] & 0b11111110
        if address_wiper0:
            if wiper0 > 0:
                wiper0 -= 1
        elif address_wiper1:
            if wiper1 > 0:
                wiper1 -= 1
    elif command_read and address_tcon:
        tcon = 0b00001000 if tcon_shutdown0 else 0b0
        tcon |= 0b00000100 if terminal_a_status0 else 0b0
        tcon |= 0b00000001 if terminal_b_status0 else 0b0
        tcon |= 0b00000010 if wiper_status0 else 0b0
        tcon |= 0b10000000 if tcon_shutdown1 else 0b0
        tcon |= 0b01000000 if terminal_a_status1 else 0b0
        tcon |= 0b00010000 if terminal_b_status1 else 0b0
        tcon |= 0b00100000 if wiper_status1 else 0b0
        read_buf[0] = (write_buf[0] | 0b00000001)
        read_buf[1] = tcon
    elif command_write and address_tcon:
        tcon = write_buf[1]
        tcon_shutdown0 = tcon & 0b00001000
        terminal_a_status0 = tcon & 0b00000100
        terminal_b_status0 = tcon & 0b00000001
        wiper_status0 = tcon & 0b00000010
        tcon_shutdown1 = tcon & 0b10000000
        terminal_a_status1 = tcon & 0b01000000
        terminal_b_status1 = tcon & 0b00010000
        wiper_status1 = tcon & 0b00100000
        read_buf[0] = (write_buf[0] | 0b00000001)
        read_buf[1] = tcon


spi_mock = mock.Mock()
spi_mock.write_readinto = write_readinto

machine_mock = mock.MagicMock()
machine_mock.Pin = mock.MagicMock()
machine_mock.SPI = mock.MagicMock(return_value=spi_mock)
patch.dict("sys.modules", machine=machine_mock).start()


class Mcp4xxxTestCase(unittest.TestCase):

    def setUp(self) -> None:
        from mcp4xxx import MCP4XXX, Pot
        self.pot0 = MCP4XXX()
        self.pot1 = MCP4XXX(pot=Pot.POT_1)

    def test_pot0_wiper_set_128_get_128(self):
        self.pot0.set(128)
        self.assertEqual(128, self.pot0.get())

    def test_pot1_wiper_set_128_get_128(self):
        self.pot1.set(128)
        self.assertEqual(128, self.pot1.get())

    def test_pot0_wiper_set_0_get_0(self):
        self.pot0.set(0)
        self.assertEqual(0, self.pot0.get())

    def test_pot1_wiper_set_0_get_0(self):
        self.pot1.set(0)
        self.assertEqual(0, self.pot1.get())

    def test_pot0_wiper_set_256_get_256(self):
        self.pot0.set(256)
        self.assertEqual(256, self.pot0.get())

    def test_pot1_wiper_set_256_get_256(self):
        self.pot1.set(256)
        self.assertEqual(256, self.pot1.get())

    def test_pot0_wiper_set_1000_get_256(self):
        self.pot0.set(1000)
        self.assertEqual(256, self.pot0.get())

    def test_pot1_wiper_set_1000_get_256(self):
        self.pot1.set(1000)
        self.assertEqual(256, self.pot1.get())

    def test_pot0_wiper_set_0_decrement_get_0(self):
        self.pot0.set(0)
        self.pot0.decrement()
        self.assertEqual(0, self.pot0.get())

    def test_pot1_wiper_set_0_decrement_get_0(self):
        self.pot1.set(0)
        self.pot1.decrement()
        self.assertEqual(0, self.pot1.get())

    def test_pot0_wiper_set_256_increment_get_256(self):
        self.pot0.set(256)
        self.pot0.increment()
        self.assertEqual(256, self.pot0.get())

    def test_pot1_wiper_set_256_increment_get_256(self):
        self.pot1.set(256)
        self.pot1.increment()
        self.assertEqual(256, self.pot1.get())

    def test_pot0_shutdown(self):
        self.pot0.set_shutdown_status(True)
        self.assertEqual(True, self.pot0.get_shutdown_status())
        self.pot0.set_shutdown_status(False)
        self.assertEqual(False, self.pot0.get_shutdown_status())

    def test_pot1_shutdown(self):
        self.pot1.set_shutdown_status(True)
        self.assertEqual(True, self.pot1.get_shutdown_status())
        self.pot1.set_shutdown_status(False)
        self.assertEqual(False, self.pot1.get_shutdown_status())

    def test_pot0_wiper_status(self):
        self.pot0.set_wiper_status(False)
        self.assertEqual(False, self.pot0.get_wiper_status())
        self.pot0.set_wiper_status(True)
        self.assertEqual(True, self.pot0.get_wiper_status())

    def test_pot1_wiper_status(self):
        self.pot1.set_wiper_status(False)
        self.assertEqual(False, self.pot1.get_wiper_status())
        self.pot1.set_wiper_status(True)
        self.assertEqual(True, self.pot1.get_wiper_status())

    def test_pot0_terminal_a_status(self):
        self.pot0.set_terminal_a_status(False)
        self.assertEqual(False, self.pot0.get_terminal_a_status())
        self.pot0.set_terminal_a_status(True)
        self.assertEqual(True, self.pot0.get_terminal_a_status())

    def test_pot1_terminal_a_status(self):
        self.pot1.set_terminal_a_status(False)
        self.assertEqual(False, self.pot1.get_terminal_a_status())
        self.pot1.set_terminal_a_status(True)
        self.assertEqual(True, self.pot1.get_terminal_a_status())

    def test_pot0_terminal_b_status(self):
        self.pot0.set_terminal_b_status(False)
        self.assertEqual(False, self.pot0.get_terminal_b_status())
        self.pot0.set_terminal_b_status(True)
        self.assertEqual(True, self.pot0.get_terminal_b_status())

    def test_pot1_terminal_b_status(self):
        self.pot1.set_terminal_b_status(False)
        self.assertEqual(False, self.pot1.get_terminal_b_status())
        self.pot1.set_terminal_b_status(True)
        self.assertEqual(True, self.pot1.get_terminal_b_status())


if __name__ == '__main__':
    unittest.main()
