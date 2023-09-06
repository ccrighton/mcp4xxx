# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: MIT
from mcp4xxx import MCP4XXX


pot = MCP4XXX()

print("Hardware shutdown status:", pot.get_hardware_shutdown_status())
pot.set_shutdown_status(True)
print("Shutdown status:", pot.get_shutdown_status())
pot.set_shutdown_status(False)
print("Shutdown status:", pot.get_shutdown_status())

pot.set_wiper_status(True)
print("Wiper connected:", pot.get_wiper_status())
pot.set_wiper_status(False)
print("Wiper connected:", pot.get_wiper_status())
print("A connected:", pot.get_terminal_a_status())
print("B connected:", pot.get_terminal_b_status())
print("Get:", str(pot.get()))
pot.set(0)
print("Get 0:", str(pot.get()))
pot.set(100)
print("Get 100:", str(pot.get()))
pot.set(256)
print("Get 256:", pot.get())
pot.decrement()
pot.decrement()
print("Get -2:", pot.get())
pot.increment()
print("Get +1:", pot.get())
