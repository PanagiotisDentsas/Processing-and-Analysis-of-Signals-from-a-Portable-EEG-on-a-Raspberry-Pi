import csv
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import welch

import csv
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import welch

# --- CONFIGURATION ---
sampling_rate = 125.0  # OpenBCI Daisy rate
num_channels = 16      # Total number of EEG channels to average

print("--- INSPiRE Global Frequency Domain Visualizer ---")
session_num = input("Enter session number : ")

base_path = f'/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session{session_num}/'
raw_filepath = base_path + 'openbcirecordings.csv'

#filt_filepath = base_path + 'filteredopenbcirecordings.csv'

#for testing
filt_filepath = base_path + 'upgraded_filtered_recordings.csv'

def load_all_channels(filename):
    """Loads columns 1 through 16 into a massive math grid."""
    data = []
    try:
        with open(filename, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader) # Skip headers
            for row in reader:
                try:
                    # Grab columns 1 through 16
                    row_vals = [float(row[i]) for i in range(1, 17)]
                    data.append(row_vals)
                except (ValueError, IndexError):
                    pass # Ignore text markers or incomplete rows
    except FileNotFoundError:
        print(f"❌ Error: Could not find file -> {filename}")
        return None
    return np.array(data)

# --- 1. Load the Data ---
print("Loading all 16 channels of data...")
raw_data = load_all_channels(raw_filepath)
filt_data = load_all_channels(filt_filepath)

if raw_data is not None and filt_data is not None:
    print("Calculating Average Power Spectral Density...")
    
    # Transpose data so it is shaped like (Channels, Samples)
    raw_data = raw_data.T
    filt_data = filt_data.T
    
    
    # --- 2. The Math Trick ---
    # Scipy can calculate all 16 channels at the exact same time (axis=1)
    f_raw, psd_raw_all = welch(raw_data, fs=sampling_rate, nperseg=250, axis=1, detrend='linear')
    f_filt, psd_filt_all = welch(filt_data, fs=sampling_rate, nperseg=250, axis=1, detrend='linear')

    # Now we average the 16 spectra together vertically (axis=0)
    psd_raw_avg = np.mean(psd_raw_all, axis=0)
    psd_filt_avg = np.mean(psd_filt_all, axis=0)

    # --- 3. Draw the Graph ---
    print("Drawing graph...")
    plt.figure(figsize=(12, 7))
    xlim_max = 60.0

    # Plot the averaged spectra
    plt.semilogy(f_raw, psd_raw_avg, label='Raw Global Average', color='red', alpha=0.5)
    plt.semilogy(f_filt, psd_filt_avg, label='Filtered Global Average', color='blue', linewidth=2)

    # Highlight Brainwave Bands
    plt.axvspan(1, 4, color='gray', alpha=0.1) # Delta
    plt.axvspan(4, 8, color='gray', alpha=0.15) # Theta
    plt.axvspan(8, 13, color='gold', alpha=0.2, label='Alpha Band (Relaxation)') 
    plt.axvspan(13, 30, color='blue', alpha=0.05, label='Beta Band (Focus)') 
    
    # Chart Styling
    plt.title("Global EEG Spectrum (Average of all 16 Channels)")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Average Power (dB/Hz)")
    plt.xlim(0, xlim_max)
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.legend()
    
    plt.show()
