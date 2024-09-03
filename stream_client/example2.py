import serial
import struct
import time

# Open serial port
ser = serial.Serial('COM3', baudrate=115200, timeout=1)

# Helper function to send BGAPI command
def send_command(command):
    ser.write(command)
    time.sleep(0.1)
    response = ser.read(ser.inWaiting())
    return response

# Function to parse advertisement data
def parse_advertisement(data):
    pos = 0
    ad_data = {}
    while pos < len(data):
        length = data[pos]
        if length == 0:
            break
        ad_type = data[pos + 1]
        ad_value = data[pos + 2:pos + 1 + length]
        ad_data[ad_type] = ad_value
        pos += 1 + length
    return ad_data

# 1. Reset dongle
reset_cmd = struct.pack('<4B', 0x20, 0x00, 0x01, 0x00)
send_command(reset_cmd)

# 2. Start scanning
start_scan_cmd = struct.pack('<6B', 0x00, 0x00, 0x01, 0x06, 0x00, 0x00)
send_command(start_scan_cmd)

print("Scanning for BLE devices...")

devices = {}

try:
    while True:
        response = ser.read(ser.inWaiting())
        if response:
            # Check if the response is an advertising report
            if response[0:2] == b'\x80\x00':  # Check for advertising report event
                ad_data = parse_advertisement(response[2:])
                if 0x09 in ad_data:  # Check for Complete Local Name (0x09)
                    name = ad_data[0x09].decode('utf-8')
                elif 0x08 in ad_data:  # Check for Shortened Local Name (0x08)
                    name = ad_data[0x08].decode('utf-8')
                else:
                    name = 'Unknown'
                
                address = response[2:8]
                address_str = ':'.join(f'{b:02X}' for b in address)
                
                if address_str not in devices:
                    devices[address_str] = name
                    print(f"Device found: {name} [{address_str}]")
except KeyboardInterrupt:
    pass

# Stop scanning (not necessary for basic scanning script, but good practice)
stop_scan_cmd = struct.pack('<4B', 0x00, 0x01, 0x01, 0x06)
send_command(stop_scan_cmd)

print("Scanning stopped.")
