
import csv
import numpy as np
import matplotlib.pyplot as plt
from brainflow.data_filter import DataFilter, FilterTypes
from scipy.signal import welch,butter, filtfilt
import matplotlib.pyplot as plt

# ==========================================
# 1. YOUR EXACT FILTER FUNCTION
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
    
    # 2. 25Hz Hardware Spike Notch (Start: 24.0 Hz, Stop: 26.0 Hz)
    DataFilter.perform_bandstop(
        np_buffer, sampling_rate, 24.5, 25.5, 1, FilterTypes.BUTTERWORTH.value, 0
    )
    
    # 3. Main Bandpass (Start: 2.0 Hz, Stop: 45.0 Hz)
    DataFilter.perform_bandpass(
        np_buffer, sampling_rate, 5.0, 45.0, 5, FilterTypes.BUTTERWORTH.value, 0
    )
    
    
    global_filtered_segment = np.mean(simulated_realtime_output, axis=0)


    chunk_length = len(new_chunk)
    
    clean_chunk = np_buffer[-chunk_length:]
    
    return clean_chunk.tolist(), history_buffer

# ==========================================
# 2. RUNNING THE LOOP
# ==========================================
if __name__ == "__main__":
    print("Loading raw CSV data...")
    
    session_num = input("Enter the session number to filter (e.g., 61): ")
    raw_path = f'/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session{session_num}/openbcirecordings.csv'
       
    channel_14_data = []

    try:
        with open(raw_path, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            for row in reader:
                try:
                    channel_14_data.append(float(row[1]))
                except:
                    pass
    except FileNotFoundError:
        print("❌ Error: Could not find the CSV file. Check the path!")
        exit()

    chunk_size = 130
    total_samples = len(channel_14_data)
    
    simulated_realtime_output = []
    my_history_buffer = []  

    print("Running modular real-time loop...")
    for start_idx in range(0, total_samples, chunk_size):
        end_idx = start_idx + chunk_size
        live_chunk = channel_14_data[start_idx:end_idx]
        
        if len(live_chunk) < chunk_size:
            break
            
        clean_live_chunk, my_history_buffer = filter_live_chunk(live_chunk, my_history_buffer)
        simulated_realtime_output.extend(clean_live_chunk)

    # ==========================================
    # 3. THE FREQUENCY DOMAIN (FFT) MATH
    # ==========================================
    print("Calculating FFT (Frequency Space)...")
    sampling_rate = 125
    
    # Ensure both arrays are exactly the same length for a fair comparison
    '''

    '''
    # 1. Grab the length of your 1D list
    data_length = len(simulated_realtime_output)

    # 2. Convert your 1D lists directly into numpy arrays
    raw_segment = np.array(channel_14_data[:data_length])
    filtered_segment = np.array(simulated_realtime_output)

    # --- Croping the Filter Startup Ringing ---
    # We slice off the first 3 seconds (375 samples) to hide the startup math.
    cutoff_samples = 3 * sampling_rate 
    
    if len(filtered_segment) > (cutoff_samples + 250):
        # Chop off the first 3 seconds of data for both lines
        raw_segment = raw_segment[cutoff_samples:]
        filtered_segment = filtered_segment[cutoff_samples:]
    # --------------------------------------------------------
    
    
    # 3. Apply Welch to the single channel
    # Using nperseg=250 (If this throws an error, change it to 125!)
    freqs, raw_fft = welch(raw_segment, fs=sampling_rate, nperseg=250, detrend='linear')
    _, filtered_fft = welch(filtered_segment, fs=sampling_rate, nperseg=250, detrend='linear')
    
    # ==========================================
    # 4. DRAWING THE GRAPH (Updated to match Script 1)
    # ==========================================
    print("Drawing Frequency Graph...")
    
    # --- 1. Set Up the Masterpiece Canvas ---
    plt.figure(figsize=(12, 8))
    plt.title("Real-Time EEG Spectrum ", fontsize=14)

    # --- 2. Plot the Lines (Forcing the Logarithmic Y-Axis) ---
    plt.semilogy(freqs, raw_fft, label="Raw Unfiltered Signal", color='red', alpha=0.5)
    plt.semilogy(freqs, filtered_fft, label="Clean Filtered Signal", color='blue', linewidth=2)

    # --- 3. Add the Colored Background Bands ---
    # Grey for Delta/Theta (0 to 8 Hz)
    plt.axvspan(0, 8, color='grey', alpha=0.15)
    
    # Yellow for Alpha Band (8 to 13 Hz)
    plt.axvspan(8, 13, color='gold', alpha=0.2, label="Alpha Band (Relaxation)")
    
    # Light Blue for Beta Band (13 to 30 Hz)
    plt.axvspan(13, 30, color='mediumslateblue', alpha=0.1, label="Beta Band (Focus)")

    # --- 4. Format the Axes and Grid ---
    plt.xlim(0, 60)  # Lock the X-axis so we only see up to 60 Hz
    plt.xlabel("Frequency (Hz)", fontsize=12, fontweight='bold')
    plt.ylabel("Average Power (dB/Hz)", fontsize=12, fontweight='bold')
    
    # Add the grid background to match the offline graph
    plt.grid(True, which="major", linestyle='-', alpha=0.6)
    plt.grid(True, which="minor", linestyle=':', alpha=0.3)
    
    # Place the legend
    plt.legend(loc='lower center', fontsize=10)

    # --- 5. Render ---
    plt.tight_layout()
    
    # If this is inside a live updating loop, use plt.pause(0.01) instead of plt.show()
    plt.show()
    
   
