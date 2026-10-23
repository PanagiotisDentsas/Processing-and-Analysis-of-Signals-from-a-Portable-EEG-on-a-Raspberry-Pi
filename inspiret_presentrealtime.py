import csv
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
from brainflow.data_filter import DataFilter, FilterTypes
from matplotlib.ticker import LinearLocator, FormatStrFormatter

# --- CONFIGURATION ---
window_size = 500  # How many samples to show on screen at once (4 seconds at 125Hz)
num_channels = 16
chunk_size = 130   # Simulate reading ~1 second of data at a time
sampling_rate = 125

print("--- INSPiRE 16-Channel Real-Time Simulator Visualizer ---")
session_num = input("Enter session number : ")

base_path = f'/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session{session_num}/'
raw_filepath = base_path + 'openbcirecordings.csv'

# ==========================================
# 1. YOUR LIVE FILTER FUNCTION (Cleaned)
# ==========================================
def filter_live_chunk(new_chunk, history_buffer, sampling_rate=125):
    history_buffer.extend(new_chunk)
    
    if len(history_buffer) > 600:
        history_buffer = history_buffer[-600:]
        
    np_buffer = np.array(history_buffer, dtype=np.float64)
    
    # 1. 50Hz Notch (Start: 48.0 Hz, Stop: 52.0 Hz)
    DataFilter.perform_bandstop(
        np_buffer, sampling_rate, 48.0, 52.0, 2, FilterTypes.BUTTERWORTH.value, 0
    )
    
    # 2. 25Hz Hardware Spike Notch (Start: 24.5 Hz, Stop: 25.5 Hz)
    DataFilter.perform_bandstop(
        np_buffer, sampling_rate, 24.5, 25.5, 1, FilterTypes.BUTTERWORTH.value, 0
    )
    
    # 3. Main Bandpass (Start: 5.0 Hz, Stop: 45.0 Hz)
    DataFilter.perform_bandpass(
        np_buffer, sampling_rate, 5.0, 45.0, 5, FilterTypes.BUTTERWORTH.value, 0
    )
    
    chunk_length = len(new_chunk)
    clean_chunk = np_buffer[-chunk_length:]
    
    return clean_chunk.tolist(), history_buffer

# ==========================================
# 2. LOAD RAW DATA
# ==========================================
def load_all_channels(filename):
    """Loads columns 1 through 16 into a massive math grid."""
    data = []
    try:
        with open(filename, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader) # Skip headers
            for row in reader:
                try:
                    row_vals = [float(row[i]) for i in range(1, 17)]
                    data.append(row_vals)
                except (ValueError, IndexError):
                    pass
    except FileNotFoundError:
        print(f"❌ Error: Could not find file -> {filename}")
        return None
    return np.array(data)

print("Loading raw CSV data...")
raw_data = load_all_channels(raw_filepath)

if raw_data is not None:
    total_samples = len(raw_data)
    print(f"Simulating real-time filtering for {total_samples} samples...")
    
    # ==========================================
    # 3. THE REAL-TIME SIMULATION LOOP
    # ==========================================
    history_buffers = [[] for _ in range(num_channels)]
    filtered_output = [[] for _ in range(num_channels)]

    for start_idx in range(0, total_samples, chunk_size):
        end_idx = start_idx + chunk_size
        live_chunk_all_channels = raw_data[start_idx:end_idx]
        
        if len(live_chunk_all_channels) == 0:
            break
            
        for ch in range(num_channels):
            ch_chunk = live_chunk_all_channels[:, ch].tolist()
            clean_ch_chunk, history_buffers[ch] = filter_live_chunk(ch_chunk, history_buffers[ch])
            filtered_output[ch].extend(clean_ch_chunk)

    # Convert output back into a Numpy grid
    filt_data = np.array(filtered_output).T

    # --- THE DIPLOMA FIX: Crop the Filter Startup Ringing ---
    # We slice off the first 3 seconds (375 samples) of the violent math swings.
    cutoff_samples = 3 * sampling_rate 
    if len(filt_data) > cutoff_samples:
        filt_data = filt_data[cutoff_samples:, :]
        
    # Update total samples to match the newly cropped data length for the slider
    total_samples_cropped = len(filt_data)
    # --------------------------------------------------------

    # ==========================================
    # 4. SCROLLABLE VISUALIZATION
    # ==========================================
    print("Drawing massive 16-row interactive graph...")
    
    fig, axes = plt.subplots(num_channels, 1, figsize=(15, 12), sharex=True)
    fig.suptitle("Simulated Live Time Domain: Filtered Data ", fontsize=16)

    # Draw EVERY sample for each row
    for i in range(num_channels):
        filt_ch = filt_data[:, i]
        
        axes[i].plot(filt_ch, color='blue', linewidth=1.5)
        
        axes[i].set_ylabel(f"Ch {i+1}", rotation=0, labelpad=25, verticalalignment='center', fontweight='bold')
        axes[i].grid(True, alpha=0.3)
        
        # --- THE CLEAN OVERLAP FIX: Dynamic Padding ---
        # 1. Find the exact minimum and maximum of this specific channel
        y_min, y_max = np.min(filt_ch), np.max(filt_ch)
        
        # (Safety check in case a channel is completely flat/dead)
        if y_max - y_min < 0.0001:
            y_min, y_max = -1.0, 1.0
            
        y_center = (y_max + y_min) / 2.0
        
        # 2. Add a 20% invisible margin above and below the wave
        margin = (y_max - y_min) * 0.20
        axes[i].set_ylim(y_min - margin, y_max + margin)
        
        # 3. Force exactly 3 ticks at the data's exact min, center, and max
        axes[i].set_yticks([y_min, y_center, y_max])
        
        # 4. Format them cleanly to 1 decimal place
        from matplotlib.ticker import FormatStrFormatter
        axes[i].tick_params(axis='y', labelsize=6)
        axes[i].yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
        # ----------------------------------------------
        

    axes[-1].set_xlabel("Samples (Time)")
    axes[0].set_xlim(0, window_size)

    # Make room at the bottom for the slider
    plt.subplots_adjust(top=0.93, bottom=0.15, hspace=0.25) 
    
    # Create slider
    ax_slider = plt.axes([0.15, 0.05, 0.7, 0.03])
    time_slider = Slider(
        ax=ax_slider,
        label='Scroll Time ',
        valmin=0,
        valmax=max(0, total_samples_cropped - window_size),
        valinit=0,
        valstep=10 
    )

    def update_window(val):
        start_point = int(time_slider.val)
        axes[0].set_xlim(start_point, start_point + window_size)
        fig.canvas.draw_idle()

    time_slider.on_changed(update_window)

    from matplotlib.lines import Line2D
    custom_lines = [Line2D([0], [0], color='blue', lw=2)]
    fig.legend(custom_lines, ['Live Filtered Data (Clean)'], loc='upper right')

    plt.show()
