import csv
import numpy as np
import matplotlib.pyplot as plt
from brainflow.data_filter import DataFilter, FilterTypes

# ==========================================
# THE INDEPENDENT REAL-TIME FILTER FUNCTION
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
# TESTING SCRIPT
# ==========================================
if __name__ == "__main__":
    print("Loading raw CSV data...")
    raw_path = '/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session28/openbcirecordings.csv'
    
    session_num = input("Enter the session number to filter (e.g., 61): ")
    
    raw_path= f'/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session{session_num}/openbcirecordings.csv'
    
    channel_1_data = []

    try:
        with open(raw_path, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            for row in reader:
                try:
                    channel_1_data.append(float(row[1]))
                except:
                    pass
    except FileNotFoundError:
        print("❌ Error: Could not find the CSV file. Check the path!")
        exit()

    chunk_size = 130
    total_samples = len(channel_1_data)
    
    # Initialize variables for the loop
    simulated_realtime_output = []
    my_history_buffer = []  # Our state memory

    print("Running modular real-time loop...")
    for start_idx in range(0, total_samples, chunk_size):
        end_idx = start_idx + chunk_size
        live_chunk = channel_1_data[start_idx:end_idx]
        
        if len(live_chunk) < chunk_size:
            break
            
        # --- THE MAGIC HAPPENS HERE ---
        # We pass the raw data and our memory to the function.
        # It hands back the clean data and the updated memory!
        clean_live_chunk, my_history_buffer = filter_live_chunk(live_chunk, my_history_buffer)
        # ------------------------------
        
        simulated_realtime_output.extend(clean_live_chunk)

    print("Drawing Verification Graph...")
    plt.figure(figsize=(12, 6))
    samples_to_view = chunk_size * 4

    for i in range(1, 5):
        plt.axvline(x=chunk_size * i, color='gray', linestyle='--', alpha=0.5)

    plt.plot(channel_1_data[:samples_to_view], label="Raw Data (Fuzzy)", color='red', alpha=0.3)
    plt.plot(simulated_realtime_output[:samples_to_view], label="Function Output (Smooth)", color='blue', linewidth=2)

    plt.title("Real time filter Function Verification")
    plt.xlabel("Samples")
    plt.ylabel("Voltage")
    plt.legend()
    plt.show()
