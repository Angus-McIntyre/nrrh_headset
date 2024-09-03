import pygatt
import time
import logging
import binascii
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import sys

#logging.basicConfig()
#logging.getLogger('pygatt').setLevel(logging.DEBUG)

def to_signed(value):
        if value > 262143:  # 2^18 - 1, max positive value for 19-bit signed int
            return value - 524288  # 2^19
        return value

adapter = pygatt.BGAPIBackend()

try:
    adapter.start()
    print("Scanning for devices...")
    scanned = adapter.scan(timeout=3)
    found_targets = [peripheral for peripheral in scanned if peripheral['name'] == 'Impulse' ]
    device = adapter.connect(found_targets[0]['address'], interval_min=6, interval_max=8)
    print("Connected to device")
    discovered_chars = device.discover_characteristics()
    print(discovered_chars)
except KeyboardInterrupt:
    adapter.stop()
except IndexError:
    print("Device not found")
    adapter.stop()
    sys.exit()

# Parameters
x_len = 400        # Number of points to display
y_range = [-16000, 16000]  # Range of possible Y values to display

# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = list(range(0, 400))
ys = [0] * x_len
ax.set_ylim(y_range)

# Create a blank line. We will update the line in animate
line, = ax.plot(xs, ys)

# Add labels
plt.title('Data Stream')
plt.xlabel('Samples')
plt.ylabel('ADC Code')

lastNum = 0

# This function is called periodically from FuncAnimation
def animate(i, ys, lastNum):
    while True:
        data = bytearray(device.char_read('00008881-0000-1000-8000-00805f9b34fb'))
        if data[0] > lastNum:
             lastNum = data[0]
             break
        else:
            print("Duplicated packet")
        
    ch1_samp1 = to_signed((data[1] | (data[2] << 8) | ((data[3] & 0x07) << 16)))
    ch1_samp2 = to_signed(((data[3] >> 3) | (data[4] << 5) | ((data[5] & 0x3F) << 13)))
    ch1_samp3 = to_signed(((data[5] >> 6) | (data[6] << 2) | (data[7] << 10) | ((data[8] & 0x01) << 18)))
    ch1_samp4 = to_signed(((data[8] >> 1) | (data[9] << 7) | ((data[10] & 0x0F) << 15)))
    ch2_samp1 = to_signed(((data[10] >> 4) | (data[11] << 4) | ((data[12] & 0x7F) << 12)))
    ch2_samp2 = to_signed(((data[12] >> 7) | (data[13] << 1) | (data[14] << 9) | ((data[15] & 0x03) << 17)))
    ch2_samp3 = to_signed(((data[15] >> 2) | (data[16] << 6) | ((data[17] & 0x1F) << 14)))
    ch2_samp4 = to_signed(((data[17] >> 5) | (data[18] << 3) | (data[19] << 11)))

    print(ch1_samp1)

    # Add y to list
    ys.append(ch1_samp1*0.001869917138805)
    ys.append(ch1_samp2*0.001869917138805)
    ys.append(ch1_samp3*0.001869917138805)
    ys.append(ch1_samp4*0.001869917138805)

    # Limit y list to set number of items
    ys = ys[-x_len:]

    # Update line with new Y values
    line.set_ydata(ys)

    return line,

# Write 0x01 to characteristic 0x8880 to start streaming
device.char_write('00008880-0000-1000-8000-00805f9b34fb', bytearray([0x01]))

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig,
    animate,
    fargs=(ys,lastNum),
    interval=0,
    blit=True)
plt.show()
