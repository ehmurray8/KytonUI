# Program Setup

## GPIB

 * Make sure the NIVisa program is installed on the target machine, this program
   enables the usage of USB GPIB hubs, and allows python to talk with the NIVisa
   program.
   - Install location: www.ni.com/download/ni-488.2/7272/en
   - The program will warn you if NIVisa is not installed when it starts
 * **Lake Shore Cryotronics 340 Default GPIB Address:** GPIB0::12::INSTR
 * **Lake Shore Cryotronics 332 Default GPIB Address:** GPIB0::13::INSTR
 * **Delta Oven Default GPIB Address:** GPIB0::27::INSTR

## Ethernet

 * Make sure the computer and all of the devices are on the same subnet.
 * **Optical Switch:** defaults to 192.168.1.111, to change the IP address and port,
   press enter, and then the down arrow 2 times, and then enter gets you to
   the IP address. Moving the arrows up and down will change the address,
   and enter will confirm the highlighted selection.
 * **Micron Optics** to change the Micron Optics IP Address, you must use the
   Micron Optics Enlight program and the network configuration can be found in
   the settings tab.