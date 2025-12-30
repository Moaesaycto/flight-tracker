# Moae's Flight Tracker

This flight tracker is a passion project that requires several pieces of equipment to work properly. Firstly, you will need to configure a RTL-SDR antenna and a GPS tracker for your device if it isn't already available. I personally use the following:

- RTL-SDR BLOG V3
- TEL0138 (GPS Tracker)

Running the `start.sh` script should automatically set everything up for you to work.

## Windows Setup

### Setting up the RTL-SDR
Linux and Mac users should be able to just run the script to begin the process, but for Windows you need to configure WSL. In PowerShell (Admin), type `wsl --install` and restart. Open Ubuntu from the Start menu and set up build tools:

```bash
sudo apt update
sudo apt install build-essential
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

Once this is set up, you should not need to repeat the process when restarting the program.

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

Once this is done, in your WSL terminal, run `ls /dev/tty*` and look for something like `/dev/ttyUSB0` or `/dev/ttyACM0`.
