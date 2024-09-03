import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class LowPassFilter:
    def __init__(self, cutoff, fs, order=5):
        nyq = 0.5 * fs
        normalized_cutoff = cutoff / nyq
        self.sos = signal.butter(order, normalized_cutoff, btype='low', output='sos')
        self.z = signal.sosfilt_zi(self.sos)
    
    def apply(self, chunk):
        filtered_chunk, self.z = signal.sosfilt(self.sos, chunk, zi=self.z)
        return filtered_chunk

def generate_signal(t):
    return np.sin(2 * np.pi * 1 * t) + 0.5 * np.sin(2 * np.pi * 10 * t) + 0.2 * np.random.randn(len(t))

# Parameters
fs = 1000  # Sampling frequency (Hz)
cutoff = 20  # Cutoff frequency (Hz)
duration = 10  # Total duration (seconds)
chunk_size = 50  # Number of samples per chunk

# Initialize filter and data
lowpass = LowPassFilter(cutoff, fs)
t = np.linspace(0, duration, int(fs * duration), endpoint=False)
signal_generator = (generate_signal(t[i:i+chunk_size]) for i in range(0, len(t), chunk_size))

# Set up the plot
fig, ax = plt.subplots(figsize=(12, 6))
line_original, = ax.plot([], [], label='Original Signal')
line_filtered, = ax.plot([], [], label='Filtered Signal')
ax.set_xlim(0, duration)
ax.set_ylim(-3, 3)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Amplitude')
ax.set_title('Real-time Low-pass Filter Demo')
ax.legend()

# Initialize data arrays
x_data, y_original, y_filtered = [], [], []

def update(frame):
    chunk = next(signal_generator)
    filtered_chunk = lowpass.apply(chunk)
    
    x_data.extend(t[frame*chunk_size:(frame+1)*chunk_size])
    y_original.extend(chunk)
    y_filtered.extend(filtered_chunk)
    
    line_original.set_data(x_data, y_original)
    line_filtered.set_data(x_data, y_filtered)
    
    return line_original, line_filtered

# Create the animation
anim = FuncAnimation(fig, update, frames=len(t)//chunk_size, interval=50, blit=True)

plt.tight_layout()
plt.show()