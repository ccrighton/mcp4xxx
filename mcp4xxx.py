# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# Ported from https://github.com/jmalloc/arduino-mcp4xxx:
# SPDX-FileCopyrightText: 2012 James Harris <contact@jamesharris.id.au>
#
# SPDX-License-Identifier: MIT
"""
 * Controls Microchip's MCP4XXX range of digital potentiometers.
 * Data Sheet: http://ww1.microchip.com/downloads/en/DeviceDoc/22060b.pdf
 *
 * Please see README.md for more information.
"""
from machine import Pin
from machine import SPI


def tobinarystr(b: bytearray) -> str:
    """ Pretty print a byte array as binary bytes separated by a space"""
    print(b)
    s = ""
    for i in range(len(b)):
        if len(s) > 0:
            s = s + " "
        s = s + f"{b[i]:08b}"
    return s


def enum(**enums):
    return type('Enum', (), enums)


# Which pot to use for dual devices (MCP42XX).
Pot = enum(POT_0=0b00, POT_1=0b01)

# The resolution of the device's resistor ladder.
Resolution = enum(RES_7BIT=127, RES_8BIT=255)

# Whether the device is a rheostat (MCP4XX2), or potentiometer (MCP4XX1).
WiperConfiguration = enum(RHEOSTAT=0, POTENTIOMETER=1)

ADDRESS_MASK = 0b11110000
COMMAND_MASK = 0b00001100
CMDERR_MASK = 0b00000010
DATA_MASK = 0b00000001
DATA_MASK_WORD = 0x01FF

TCON_SHUTDOWN_MASK = 0b1000
TCON_TERM_A_MASK = 0b0100
TCON_TERM_B_MASK = 0b0001
TCON_WIPER_MASK = 0b0010

STATUS_SHUTDOWN_MASK = 0b10

ADDRESS_POT0_WIPER = 0b0000
ADDRESS_POT1_WIPER = 0b0001
ADDRESS_TCON = 0b0100
ADDRESS_STATUS = 0b0101

COMMAND_WRITE = 0b00
COMMAND_READ = 0b11
COMMAND_INCREMENT = 0b01
COMMAND_DECREMENT = 0b10


class MCP4XXX:

    SS = 17

    """
    pot         - For the 2-pot variants (MCP42XX), the potentiometer to control. Must be pot_0 for MCP41XX chips.
    resolution  - res_7bit for MCP4X3X and MCP4X4X, res_8bit for MCP4X5X and MCP4X6X.
    """

    def __init__(self, spi=None, select_pin=SS, pot=Pot.POT_0, resolution=Resolution.RES_8BIT,
                 config=WiperConfiguration.POTENTIOMETER):
        """
        :param spi: SPI interface, machine.SPI hardware spi by default
        :param pot: For the 2-pot variants (MCP42XX), the potentiometer to control. Must be pot_0 for MCP41XX chips.
        :param resolution: res_7bit for MCP4X3X and MCP4X4X, res_8bit for MCP4X5X and MCP4X6X.
        :param config: POTENTIOMETER or REOSTAT
        """
        self.spi = spi
        self.m_pot = pot
        self.resolution = resolution
        self.config = config
        self.m_select_pin = Pin(select_pin, mode=Pin.OUT, value=1)
        self.m_select_nesting: int = 0

        bits = 7 if self.resolution == Resolution.RES_7BIT else 8

        # If spi not already initialised then use default hardware SPI
        if not self.spi:
            self.spi = SPI(0)
            self.spi.init(baudrate=250_000)

    def __repr__(self):
        return f"MCP4XXX(pot={self.m_pot}, resolution={self.resolution}, " + \
               f"wiper={'POTENTIOMETER' if self.config else 'RHEOSTAT'}, spi={self.spi}"

    def max_value(self):
        """
        Retrieve the maximum value allowed for the wiper position.

        The maximum value depends on the device's resolution and wiper configuration.

        7-bit devices have a maximum value of 127 for rheostats and 128 for potentiometers.
        8-bit devices have a maximum value of 255 for rheostats and 256 for potentiometers.

        The higher value on potentiometers (MCP4XX1) facilitates direct connection of the wiper
        to the "A" terminal (also known as "full-scale").

        Confusingly the rheostat devices (MCP4XX2) have only a wiper pin and "B" terminal pin, (not "A").
        """
        return self.resolution + self.config

    def increment(self):
        """
        Increase the wiper position by 1.
        :return: True on success; otherwise, False.
        """
        address = ADDRESS_POT0_WIPER if self.m_pot == Pot.POT_0 else ADDRESS_POT1_WIPER
        self._transfer(address, COMMAND_INCREMENT)

    def decrement(self):
        """
        Decrease the wiper position by 1.
        :return: True on success; otherwise, False.
        """
        address = ADDRESS_POT0_WIPER if self.m_pot == Pot.POT_0 else ADDRESS_POT1_WIPER
        self._transfer(address, COMMAND_DECREMENT)

    def set(self, value: int):
        """
        Set the wiper position.
        :param value: The new wiper position (must be between 0 and max_value()).
        :exception: exception on failure to set wiper position
        """
        address = ADDRESS_POT0_WIPER if self.m_pot == Pot.POT_0 else ADDRESS_POT1_WIPER
        self._transfer(address, COMMAND_WRITE, min(value, self.max_value()))

    def get(self) -> int:
        """
        Get the wiper position.
        :returns: current wiper position
        :exception: exception on failure to get wiper position
        """
        address = ADDRESS_POT0_WIPER if self.m_pot == Pot.POT_0 else ADDRESS_POT1_WIPER
        resp = self._transfer(address, COMMAND_READ, DATA_MASK_WORD)
        return resp[1] | (resp[0] & 0b00000001) << 8

    def set_terminal_a_status(self, connected: bool):
        """
        Set the status of terminal "A".
        This method will always fail on rheostat (MCP4XX2) devices.
        Use set_terminal_b_status() instead.

        :param connected: True to connect, False to disconnect
        :return: True on success, otherwise False
        """
        self._set_tcon_bit(TCON_TERM_A_MASK, connected)

    def get_terminal_a_status(self) -> bool:
        """
        Get the status of terminal "A".

        This method will always fail on rheostat (MCP4XX2) devices.
        Use get_terminal_b_status() instead.

        :return: True if the command is successful AND the terminal is connected; otherwise FALSE.
        """
        return bool(self._get_tcon_bit(TCON_TERM_A_MASK))

    def set_terminal_b_status(self, connected: bool):
        """
        Set the status of terminal "B".
        :param connected: True to connect, False to disconnect
        :return: True on success, otherwise False
        """
        self._set_tcon_bit(TCON_TERM_B_MASK, connected)

    def get_terminal_b_status(self) -> bool:
        """
        Get the status of terminal "B".

        :return: True if the command is successful AND the terminal is connected; otherwise FALSE.
        """
        return bool(self._get_tcon_bit(TCON_TERM_B_MASK))

    def set_wiper_status(self, connected: bool):
        """
        Set the status of the wiper.

        :param connected: True to connect, False to disconnect
        :exception: exception on failure
        """
        self._set_tcon_bit(TCON_WIPER_MASK, connected)

    def get_wiper_status(self) -> bool:
        """
        Get the status of the wiper.

        :return: True if wiper is connected otherwise false
        :exception: command failed
        """
        return bool(self._get_tcon_bit(TCON_WIPER_MASK))

    def set_shutdown_status(self, shutdown: bool):
        """
        Set the software shutdown status.
        :param shutdown: True to shutdown, False to enable
        :exception: failed to perform command
        """
        self._set_tcon_bit(TCON_SHUTDOWN_MASK, not shutdown)

    def get_shutdown_status(self) -> bool:
        """
        Get the software shutdown status.
        Note that although the shutdown behaviour is overridden by the hardware SHDN pin (if present),
        this method will still return the software setting. To get the hardware status use
        get_hardware_shutdown_status().

        :return: device software shutdown state
        :exception: command not successful
        """
        return not bool(self._get_tcon_bit(TCON_SHUTDOWN_MASK))

    def get_hardware_shutdown_status(self) -> bool:
        """
        Get the status of the hardware shutdown bin, if present.

        :return: True if shutdown, False if enabled
        :exception: command not successful
        """
        return bool(self._transfer(ADDRESS_STATUS,
                                   COMMAND_READ, DATA_MASK_WORD)[1] & STATUS_SHUTDOWN_MASK)

    def _select(self):
        """
        Select this device for SPI communication
        Configures SPI for communication with MCP devices, and sends slave-select pin LOW.
        """
        self.m_select_nesting += 1
        if self.m_select_nesting == 1:
            self.m_select_pin(0)

    def _deselect(self):
        """
        Cease SPI communications with this device.
        Sends the slave-select pin HIGH.
        """
        self.m_select_nesting -= 1
        if self.m_select_nesting == 0:
            self.m_select_pin(1)

    def _build_command(self, address, command, data: int = None) -> bytearray:
        """
        Build an 8-bit command
        :param address:
        :param command:
        :return:
        """
        cmd = bytearray(1)
        cmd[0] = (((address << 4) & ADDRESS_MASK) | ((command << 2) & COMMAND_MASK) | CMDERR_MASK)
        if data is not None:
            cmd.append((data & DATA_MASK_WORD) & 0xFF)
            # Handle the case where the data is 256 (full scale) or 0x1FF (DATA_MASK_WORD) - 9th bit is set
            if data == 0x0100 or data == 0x01FF:
                cmd[0] = cmd[0] | 0b00000001
        return cmd

    def _transfer(self, address, command, data: int = None) -> bytes:
        f"""
        Transfer a command, and read the response.

        :param address: 4 bit address code from ADDRESS_TCON, ADDRESS_MASK, ADDRESS_STATUS,
                        ADDRESS_POT0_WIPER, ADDRESS_POT1_WIPER
        :param command: 2 bit command code from COMMAND_WRITE, COMMAND_READ,
                        COMMAND_INCREMENT, COMMAND_DECREMENT
        :param data: data for command
        :return: bytearray response
        """
        cmd = self._build_command(address, command, data)
        rx_data = bytearray(len(cmd))
        try:
            self._select()
            self.spi.write_readinto(cmd, rx_data)
        finally:
            self._deselect()
        return rx_data

    def _set_tcon(self, value: int):
        """
        Set the value of the TCON register.
        :param value: single byte value of TCON register
        """
        # Note that the 9th (reserved) bit is always set to 1.
        self._transfer(ADDRESS_TCON, COMMAND_WRITE, 0x100 | value)

    def _set_tcon_bit(self, mask: int, value: bool):
        """
        Set the value of a bit within the TCON register.

        :param mask: One of the TCON bit masks.
        :param value: The value of the TCON bit for the given mask.
        :exception: if failed
        """
        try:
            self._select()

            # The values for pot #1 are 4 bits higher in the TCON register.
            if self.m_pot == Pot.POT_1:
                mask <<= 4

            tcon = self._get_tcon()
            if value:
                self._set_tcon(tcon | mask)
            else:
                self._set_tcon(tcon & (~mask & 0xFF))
        finally:
            self._deselect()

    def _get_tcon(self) -> int:
        """
        Get the value of the TCON register
        :return: value of the TCON register
        :exception: on failure
        """
        return self._transfer(ADDRESS_TCON, COMMAND_READ, DATA_MASK_WORD)[1]

    def _get_tcon_bit(self, mask: int) -> bool:
        """
        Get the value of the TCON register bit

        :param mask: One of the TCON bit masks.
        :return: Assigned the value of the TCON bit for the given mask.
        :exception: on failure
        """
        tcon = self._get_tcon()
        # The values for pot #1 are 4 bits higher in the TCON register.
        if self.m_pot == Pot.POT_1:
            mask <<= 4

        return tcon & mask
