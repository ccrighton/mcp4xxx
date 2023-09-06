<!--
SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.nz>

SPDX-License-Identifier: MIT
-->

# micropython-mcp4xxx

Micropython library for controlling [Microchip's MCP4XXX](http://ww1.microchip.com/downloads/en/DeviceDoc/22060b.pdf) range of SPI controlled digital potentiometers.

## Supported Devices

The supported chips are designated as follows:

```
MCP 4 X Y Z
      │ │ │
      │ │ └── (Z) Wiper Configuration
      │ │         1 = Potentiometer, 2 = Rheostat
      │ │
      │ └──── (Y) Memory Type / Resolution
      │           3 = 7-bit RAM, 4 = 7-bit EEPROM, 5 = 8-bit RAM, 6 = 8-bit EEPROM
      │
      └────── (X) Number of pots
                  1 or 2
```

This encompasses: MCP4131, MCP4151, MCP4231, MCP4251, MCP4132, MCP4152, MCP4232 and MCP4252.

### SPI connection on MCP4X1X

Note that the MCP41X1 chips multiplex SDI and SDO on a single pin. To use these chips with a standard SPI interface as on the Arduino you will need to
connect the shared SDI/SDO pin on the pot to the Arduino's MISO pin, then bridge the MISO pin to the MOSI pin with a resistor (3k9 resistor seems to work well).

## Installation

 * Download the library (a list of available versions is [here](https://github.com/ccrighton/micropython-mcp4xxx/releases))


## Example

```python
from mcp4xxx import MCP4XXX


pot = MCP4XXX()

print("Shutdown status:", pot.get_shutdown_status())
print("Wiper connected:", pot.get_wiper_status())
print("A connected:", pot.get_terminal_a_status())
print("B connected:", pot.get_terminal_b_status())
print("Get wiper:", str(pot.get()))
print("Set wiper to 0")
pot.set(0)
print("Get wiper:", str(pot.get()))
print("Set wiper to 100")
pot.set(100)
print("Get wiper:", str(pot.get()))
print("Set wiper to 255")
pot.set(255)
print("Get wiper:", str(pot.get()))
print("Decrement wiper twice")
pot.decrement()
pot.decrement()
print("Get wiper:", str(pot.get()))
print("Increment wiper")
pot.increment()
print("Get wiper:", str(pot.get()))

```

The `MCP4XXX` class supports the full range of commands available on the MCP4XXX range of devices,
for more information please see the API documentation in the [modeule](mcp4xxx.py).

## Known Issues / Caveats

* Does not support entire 4XXX range, notably absent is support for I2C and quad-pot devices.
* Only tested with MCP4151, which does not have a hardware shutdown pin.

# Credits

James Harris, https://github.com/jmalloc/arduino-mcp4xxx, MIT License
