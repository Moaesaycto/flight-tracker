import socket

# parts[0] = "MSG" - Message type
# parts[1] = "3" - Transmission type (1-8, each means different data)
# parts[2] = "1" - Session ID
# parts[3] = "1" - Aircraft ID
# parts[4] = "ABC123" - Hex ICAO address (unique aircraft identifier)
# parts[5] = "1" - Flight ID
# parts[6] = "2024/12/26" - Date message generated
# parts[7] = "14:23:45.123" - Time message generated
# parts[8] = "2024/12/26" - Date message logged
# parts[9] = "14:23:45.456" - Time message logged
# parts[10] = "UAL123" - Callsign/Flight number
# parts[11] = "38000" - Altitude (feet)
# parts[12] = "450" - Ground speed (knots)
# parts[13] = "123.456" - Track/heading (degrees)
# parts[14] = "-78.901" - Latitude
# parts[15] = "45.123" - Longitude
# parts[16] = "" - Vertical rate (feet/min)
# parts[17] = "" - Squawk code
# parts[18] = "0" - Alert flag
# parts[19] = "0" - Emergency flag
# parts[20] = "0" - SPI flag
# parts[21] = "0" - Is on ground


class FlightTracker:
    def on_update(self, aircraft_data):
        """Process aircraft data"""
        print(f"Update: {aircraft_data}")

def parse_sbs_message(line):
    parts = line.split(',')
    
    if len(parts) < 22:
        return None
    
    msg_type = parts[1]
    
    # Type 3 has position data
    if msg_type == '3':
        return {
            'icao': parts[4],
            'callsign': parts[10].strip() if parts[10] else None,
            'altitude': int(parts[11]) if parts[11] else None,
            'latitude': float(parts[14]) if parts[14] else None,
            'longitude': float(parts[15]) if parts[15] else None,
        }
    
    # Type 4 has velocity data
    elif msg_type == '4':
        return {
            'icao': parts[4],
            'callsign': parts[10].strip() if parts[10] else None,
            'ground_speed': int(parts[12]) if parts[12] else None,
            'heading': float(parts[13]) if parts[13] else None,
            'vertical_rate': int(parts[16]) if parts[16] else None,
        }
    
    return None

def listen_to_dump1090():
    tracker = FlightTracker()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 30003))
    
    buffer = ""
    
    while True:
        # Receive data from the socket
        data = sock.recv(1024).decode('utf-8')
        buffer += data
        
        # Process complete lines
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            print(line)
            """ if line.startswith('MSG'):
                aircraft = parse_sbs_message(line)
                if aircraft:
                    tracker.on_update(line) """


import serial
import pynmea2

def get_gps_location():
    port = "/dev/ttyACM0"
    baud = 9600
    
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print("Connected to GPS. Waiting for lock...")
        
        while True:
            line = ser.readline().decode('ascii', errors='replace')
            
            # Check if the line is a GGA sentence (which contains position)
            if line.startswith('$GPGGA'):
                try:
                    msg = pynmea2.parse(line)
                    
                    # msg.gps_qual == 0 means no fix
                    if msg.gps_qual > 0:
                        print(f"Latitude: {msg.latitude:.6f}")
                        print(f"Longitude: {msg.longitude:.6f}")
                        print(f"Altitude: {msg.altitude} {msg.altitude_units}")
                        print(f"Satellites: {msg.num_sats}")
                        return msg.latitude, msg.longitude
                    else:
                        print(f"Waiting for fix... (Sats visible: {msg.num_sats})", end='\r')
                except pynmea2.ParseError:
                    continue
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    listen_to_dump1090()
    # get_gps_location()
    # app = QApplication