import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import threading
import queue
import time
import pygatt
import time
import sys

def to_signed(value):
        if value > 262143:  # 2^18 - 1, max positive value for 19-bit signed int
            return value - 524288  # 2^19
        return value

class LowPassFilter:
    def __init__(self, cutoff, fs, order=5):
        nyq = 0.5 * fs
        normalized_cutoff = cutoff / nyq
        self.sos = signal.butter(order, normalized_cutoff, btype='low', output='sos')
        self.z = signal.sosfilt_zi(self.sos)
    
    def apply(self, chunk):
        filtered_chunk, self.z = signal.sosfilt(self.sos, chunk, zi=self.z)
        return filtered_chunk

class DataSource:
    def __init__(self, fs, chunk_size):
        self.fs = fs
        self.chunk_size = chunk_size
        self.current_time = 0

    def get_data(self):
        t = np.linspace(self.current_time, self.current_time + self.chunk_size/self.fs, self.chunk_size, endpoint=False)
        chunk = np.sin(2 * np.pi * 1 * t) + 0.5 * np.sin(2 * np.pi * 10 * t) + 0.2 * np.random.randn(len(t))
        self.current_time += self.chunk_size/self.fs
        return chunk

def data_producer(device, data_source, data_queue, stop_event):
    lastNum = 0
    device.char_write('00008880-0000-1000-8000-00805f9b34fb', bytearray([0x01]))
    while not stop_event.is_set():
        #data = data_source.get_data()
        #data_queue.put(data)
        #time.sleep(0.05)  # Simulate data acquisition time
        while True:
            data = bytearray(device.char_read('00008881-0000-1000-8000-00805f9b34fb'))
            print(data[0])
            if data[0] != lastNum:
                lastNum = data[0]
                break
            else:
                print(f"Duplicated packet. Lastnum was {lastNum} and data[0] was {data[0]}")
        
        ch1_samp1 = to_signed((data[1] | (data[2] << 8) | ((data[3] & 0x07) << 16)))
        ch1_samp2 = to_signed(((data[3] >> 3) | (data[4] << 5) | ((data[5] & 0x3F) << 13)))
        ch1_samp3 = to_signed(((data[5] >> 6) | (data[6] << 2) | (data[7] << 10) | ((data[8] & 0x01) << 18)))
        ch1_samp4 = to_signed(((data[8] >> 1) | (data[9] << 7) | ((data[10] & 0x0F) << 15)))
        ch2_samp1 = to_signed(((data[10] >> 4) | (data[11] << 4) | ((data[12] & 0x7F) << 12)))
        ch2_samp2 = to_signed(((data[12] >> 7) | (data[13] << 1) | (data[14] << 9) | ((data[15] & 0x03) << 17)))
        ch2_samp3 = to_signed(((data[15] >> 2) | (data[16] << 6) | ((data[17] & 0x1F) << 14)))
        ch2_samp4 = to_signed(((data[17] >> 5) | (data[18] << 3) | (data[19] << 11)))

        ys = np.array([])

        # Add y to list using numpy.append
        ys = np.append(ys, ch1_samp1 * 0.001869917138805)
        ys = np.append(ys, ch1_samp2 * 0.001869917138805)
        ys = np.append(ys, ch1_samp3 * 0.001869917138805)
        ys = np.append(ys, ch1_samp4 * 0.001869917138805)

        data_queue.put(ys)


adapter = pygatt.BGAPIBackend()
def ble_init():
    global device
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
fs = 200  # Sampling frequency (Hz)
cutoff = 35  # Cutoff frequency (Hz)
display_duration = 10  # Duration to display on screen (seconds)
chunk_size = 4  # Number of samples per chunk

# Initialize BLE
ble_init()

# Initialize filter and data
lowpass = LowPassFilter(cutoff, fs)
display_size = int(display_duration * fs)
t = np.linspace(0, display_duration, display_size, endpoint=False)

# Set up the plot
fig, ax = plt.subplots(figsize=(12, 6))
line_original, = ax.plot([], [], label='Original Signal')
line_filtered, = ax.plot([], [], label='Filtered Signal')
ax.set_xlim(0, display_duration)
ax.set_ylim(-1000, 1000)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Amplitude')
ax.set_title('Threaded Low-pass Filter Demo')
ax.legend()

# Initialize circular buffers
original_buffer = deque(maxlen=display_size)
filtered_buffer = deque(maxlen=display_size)

# Initialize with zeros
original_buffer.extend(np.zeros(display_size))
filtered_buffer.extend(np.zeros(display_size))

# Set up the data source and queue
data_source = DataSource(fs, chunk_size)
data_queue = queue.Queue()
stop_event = threading.Event()

# Start the stream
device.char_write('00008880-0000-1000-8000-00805f9b34fb', bytearray([0x01]))

# Start the data producer thread
producer_thread = threading.Thread(target=data_producer, args=(device, data_source, data_queue, stop_event))
producer_thread.start()

def update(frame):
    try:
        chunk = data_queue.get_nowait()
        filtered_chunk = lowpass.apply(chunk)
        
        # Extend buffers with new data
        original_buffer.extend(chunk)
        filtered_buffer.extend(filtered_chunk)
        
        # Update plot data
        line_original.set_data(t, list(original_buffer))
        line_filtered.set_data(t, list(filtered_buffer))
    except queue.Empty:
        pass  # No new data available
    
    return line_original, line_filtered

# Create the animation
anim = FuncAnimation(fig, update, interval=0, blit=True)

plt.tight_layout()
plt.show()

# Clean up
stop_event.set()
producer_thread.join()