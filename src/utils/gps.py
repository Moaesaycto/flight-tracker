from typing import Tuple

import serial
import pynmea2
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def get_gps_location() -> Tuple[float, float]:
    if config.get('GPS', 'type') == "auto":
        port = config.get('GPS', 'port')
        baud = config.getint('GPS', 'baud')
        try:
            with serial.Serial(port, baud, timeout=1) as ser:
                print("Connected to GPS. Waiting for lock...")

                while True:
                    line = ser.readline().decode('ascii', errors='replace')

                    if line.startswith('$GPGGA'):
                        try:
                            msg = pynmea2.parse(line)
                            if msg.gps_qual and int(msg.gps_qual) > 0 and msg.latitude and msg.longitude:
                                return float(msg.latitude), float(msg.longitude)
                            else:
                                print(
                                    f"Waiting for fix... (Sats visible: {msg.num_sats})", end='\r')
                        except pynmea2.ParseError:
                            continue

        except Exception as e:
            print(f"Serial Error: {e}")
            return config.getfloat('GPS', 'lat'), config.getfloat('GPS', 'lon')

    return config.getfloat('GPS', 'lat'), config.getfloat('GPS', 'lon')
