# Moae's Flight Tracker

**Type:** Application / Live Tracker · **Tech Stack:** PySide6, OpenGL · **Hardware:** RTL-SDR, GPS · **Status:** Active


## **Overview**

This flight tracker has been designed to track planes without the need of external APIs or even an internet connection. You connect the relevant pieces of hardware and run `start.sh`, and it should automatically set everything up for you. I personally use the following:

- RTL-SDR BLOG V3
- TEL0138 (GPS Tracker)

This software is still in active development and is not ready for actual use.

### **Features**

Tracking is done with [dump1090](https://github.com/antirez/dump1090) and GPS tracking is done through [pynmea2](https://github.com/Knio/pynmea2). Follow the setup below to set up the hardware and prepare the config file, and simply run the `start.sh` script to get it up and running. Enjoy!

### **Purpose**

This software is a passion project. I enjoy working with complex systems and live simulations/tracking, and this felt like the perfect blend that connects my other passion for aviation and aerospace. The software in this project is also intentionally complicated because I wanted to strengthen my knowledge of OpenGL and PySide6.

## Windows Setup

### Setting up the RTL-SDR
Linux and Mac users should be able to just run the script to begin the process, but for Windows you need to configure WSL. In PowerShell (Admin), type `wsl --install` and restart. Open Ubuntu from the Start menu and set up build tools:

```bash
sudo apt update
sudo apt install build-essential
```

Install the tools required for WSL to accept USB devices:

```bash
sudo apt install linux-tools-virtual hwdata
sudo update-alternatives --install /usr/local/bin/usbip usbip /usr/lib/linux-tools/*/usbip 20
```

Now we need to configure the USB bus to make sure that WSL can actually read the data from the antenna. On your powershell terminal, run

```powershell
winget install usbipd
usbipd list
````

You should see something like:

```
Connected:
BUSID  VID:PID    DEVICE                                                        STATE
X-X    1234:abcd  Bulk-In, Interface                                            Not shared
```

Look for "Bulk-In, Interface" or "RTL2838" or similar and note the BUSID (the `X-X` in the example above, where the Xs should be numbers). In PowerShell, bind it:

```powershell
usbipd bind --busid X-X
```

**Important:** You only need to `bind` the device once. Every time you restart your computer or reconnect hardware, you must run the attach command again to bring it into Ubuntu.

### Connecting the RTL-SDR to the WSL Environment
To actually connect it to WSL, run the following:

```PowerShell
usbipd attach --wsl --busid X-X
```

You can check to see if it is actually in the WSL system by running `lsusb`.

### Setting up the GPS

Just like you did before, list out the connected USB modules (using `usbipd list`) and look for the GPS (usually `COM3`, `COM4`, etc.)

```powershell
Connected:
BUSID  VID:PID    DEVICE                                                        STATE
Y-Y    dead:beef  USB Serial Device (COM3)                                      Not shared
X-X    1234:abcd  Bulk-In, Interface                                            Attached
```

Just like last time, bind and attach it:

```powershell
usbipd bind --busid Y-Y
usbipd attach --wsl --busid Y-Y
```

You now need to find the port for the GPS connection, which can be done with the following methods:

* **Windows (WSL2):** We will cover two ways:
  * In your WSL terminal, run `ls /dev/tty*` and look for the port. It should look something like `/dev/ttyUSB0` or `/dev/ttyACM0`.
  * After running the `attach` command, run `dmesg | grep tty` in your WSL terminal. Look for a line that says `attached to ttyUSB0` or `ttyACM0`. Your port is `/dev/ttyUSB0` (or `/dev/ttyACM0` respectively).
* **Mac:** Run `ls /dev/cu.usb*` and look for the connection. It should look something like `/dev/cu.usbmodem2101`.
* **Linux:** Untested, but see Windows as it's probably the same as WSL.

To verify if it is actually connected, consider using a tool like [u-center](https://www.u-blox.com/en/product/u-center) (for Windows) or [PyGPSClient](https://github.com/semuconsulting/PyGPSClient). To check if it's running without downloading more software, consider running `screen port/from/before` but replace it with your port.

Update the port in the `config.ini` configuration file.