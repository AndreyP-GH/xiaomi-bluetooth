# xiaomi-mijia2


## Overview
The xiaomi-mijia2 Python module provides interaction capabilities with Xiaomi Mijia2 temperature and humidity sensors (model Lywsd03mmc) using Tango Controls via PyTango module. It allows incorporating the Mijia2 Lywsd03mmc into Tango environment, communicating with it separately or via macros or script during an experiment. 
Its primapy function is to poll one or multiple Lywsd03mmc sensors and receive its data:
- temperature
- humidity
- battery

The xiaomi-mijia2 supports only sequential use/polling of sensors. 
Connection and retrieving information from each sensor takes up to 10 seconds which is dictated by the speed of bluetooth protocol and the performance of a sensor itself. 
The number of connected sensors is theoretically unlimited but is subject to expediency and the needs of a particular experiment. 


## Prerequisites
It is implied that the client/operator has at his disposal a Linux-based computer, Python3 and corresponding version of pip installed.  
The xiaomi-mijia2 is a noarch package and is suitable for all currently supported implementations of Linux OS. 
It is worth pointing out that the xiaomi-mijia2 module runs on Linux only since the bluepy module used in the program cannot be installed on OS other than Linux. 


## Additional Software Documentation
Useful links:
- [Tango Controls](https://tango-controls.readthedocs.io/en/latest/)
- [PyTango](https://pytango.readthedocs.io/en/stable/)


## Installation
**The installation command implies installation of the package with its three required dependencies: [btmgmt](https://github.com/BOJIT/btmgmt), [lywsd03mmc](https://github.com/uduncanu/lywsd03mmc) and [PyTango](https://pytango.readthedocs.io/en/stable/).**

Clone the repository to the desired directory.

Install the package globally. Execute from a package directory:  
`sudo python3 -m pip install .`

List all the globally installed packages:  
`sudo pip list`

Uninstall the package via pip:  
`sudo pip uninstall xiaomi-mijia2 -y`

Uninstall the package and its dependencies lywsd03mmc and btmgmt:  
`sudo pip uninstall xiaomi-mijia2 lywsd03mmc btmgmt -y`


## Author
Andrey Pechnikov


## License
MIT License


## Project status
Stable release, v. 1.0.  
No further development planned as of Jan, 2024.


## Nota bene
Built and tested with Python 3.9. Python 2 untested.  
Tested on Raspberry Pi 3B under AlmaLinux 9.3.  

Lines 29-46 automatically parse all the available bluetooth controllers  
and put them into dict "bt_interface" as keys, where their values are their HCIs.  
When launched from Astor (tangosys user) this code doesn't perform as planned.
For this reason these lines are muted and mac addresses with corresponding HCIs
are hardcoded in line 28.
Mac address of a bluetooth controller and an HCI must be updated in this dict.  

Mac addresses of each Xiaomi Lywsd03mmc sensor must be specified via Jive in Tango database as "mac_address" device property.