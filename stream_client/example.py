import pygatt
import time
import logging
import binascii

def to_signed(value):
        if value > 262143:  # 2^18 - 1, max positive value for 19-bit signed int
            return value - 524288  # 2^19
        return value

#logging.basicConfig()
#logging.getLogger('pygatt').setLevel(logging.DEBUG)

# The BGAPI backend will attempt to auto-discover the serial device name of the
# attached BGAPI-compatible USB adapter.
adapter = pygatt.BGAPIBackend()

try:
    adapter.start()
    scanned = adapter.scan(timeout=2)
    found_targets = [peripheral for peripheral in scanned if peripheral['name'] == 'Impulse' ]
    device = adapter.connect(found_targets[0]['address'], interval_min=6, interval_max=6)
    discovered_chars = device.discover_characteristics()
    print(discovered_chars)
    count = 0
    # Write 0x01 to characteristic 0x8880 to start streaming
    device.char_write('00008880-0000-1000-8000-00805f9b34fb', bytearray([0x01]))
    #start = time.time()
    #for _ in range(100):
    start = time.time()
    recvcnt = 0
    packet = device.char_read('00008881-0000-1000-8000-00805f9b34fb')
    lastval = packet[0]
    while True:
        #packet = device.char_read('00008881-0000-1000-8000-00805f9b34fb')

        #chan1 = int.from_bytes(packet[0], byteorder='little', signed = True)
        #print(packet[0])
        recvcnt += 1
        end = time.time()
        #print((time.time()- start)/recvcnt)
        #print(f"{binascii.hexlify(bytearray(device.char_read('00008881-0000-1000-8000-00805f9b34fb')))}")

        data = bytearray(device.char_read('00008881-0000-1000-8000-00805f9b34fb'))

        ch1_samp1 = to_signed((data[1] | (data[2] << 8) | ((data[3] & 0x07) << 16)))
        ch1_samp2 = to_signed(((data[3] >> 3) | (data[4] << 5) | ((data[5] & 0x3F) << 13)))
        ch1_samp3 = to_signed(((data[5] >> 6) | (data[6] << 2) | (data[7] << 10) | ((data[8] & 0x01) << 18)))
        ch1_samp4 = to_signed(((data[8] >> 1) | (data[9] << 7) | ((data[10] & 0x0F) << 15)))
        ch2_samp1 = to_signed(((data[10] >> 4) | (data[11] << 4) | ((data[12] & 0x7F) << 12)))
        ch2_samp2 = to_signed(((data[12] >> 7) | (data[13] << 1) | (data[14] << 9) | ((data[15] & 0x03) << 17)))
        ch2_samp3 = to_signed(((data[15] >> 2) | (data[16] << 6) | ((data[17] & 0x1F) << 14)))
        ch2_samp4 = to_signed(((data[17] >> 5) | (data[18] << 3) | (data[19] << 11)))



        print(f'{ch1_samp1}\t{ch2_samp1}')
        print(f'{ch1_samp2}\t{ch2_samp2}')
        print(f'{ch1_samp3}\t{ch2_samp3}')
        print(f'{ch1_samp4}\t{ch2_samp4}')

        #count += 1
        #device.char_read('00008881-0000-1000-8000-00805f9b34fb')
        #time.sleep(1)
    #end = time.time()
    #print(end - start)

finally:
    adapter.stop()