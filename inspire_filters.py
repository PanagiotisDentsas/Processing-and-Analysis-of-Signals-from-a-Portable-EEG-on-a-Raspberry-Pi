



import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

from brainflow.data_filter import DataFilter, FilterTypes

def apply_frequency_filters(number_data):
    """
    Takes raw CSV numbers, applies Notch and Bandpass filters to the EEG columns,
    and returns the cleaned numbers ready to be saved.
    """
    print('Applying  filters ')
    
    # 1. Convert the text data into a NumPy grid of numbers so we can do math
    data = np.array(number_data, dtype=float)

    # ==========================================
    #️ SETTINGS (Super easy to change)
    # ==========================================
    fs = 125.0              # Sampling Rate (125 Hz for 16-channel Cyton+Daisy)
    
    # Notch Filter Settings (Removes electrical hum)
    notch_freq = 50.0       # 50Hz for Europe/Most of world
    quality_factor = 30.0   # How "sharp" the notch cut is
    
    # Bandpass Filter Settings (Keeps only actual brainwaves)
    lowcut = 3.0            # Bottom frequency (3 Hz removes slow eye blinks)
    highcut = 40.0          # Top frequency (40 Hz removes fast muscle tension)
    
    # Columns to filter
    eeg_start_col = 1       # Fp1 is at index 1
    eeg_end_col = 16        # P4 is at index 16
    # ==========================================


    # 2. Create the Math Filters using SciPy
    nyq = 0.5 * fs # Nyquist Frequency (Required for the math)
    
    # Build the Notch 50hz filter
    b_notch, a_notch = iirnotch(notch_freq, quality_factor, fs)
    
    #non standart 25hz filter
    b_notch25, a_notch25 = iirnotch(w0=25.0, Q=52.0, fs=125)
    
    # Build the Bandpass (4th order Butterworth)
    low = lowcut / nyq
    high = highcut / nyq
    b_band, a_band = butter(4, [low, high], btype='band')


    # 3. Apply the filters strictly to the EEG columns
    # We use a loop to go through columns 1 to 16, one by one
    for col in range(eeg_start_col, eeg_end_col + 1):
        
        # Grab the entire vertical column of data for just this one brainwave channel
        channel_data = data[:, col]
        
        # Scrub it with the Notch filter
        channel_data = filtfilt(b_notch, a_notch, channel_data)
        # Scrub it with the 25 Hz Notch filter
        channel_data = filtfilt(b_notch25, a_notch25, channel_data)
        
        # Scrub it with the Bandpass filter
        channel_data = filtfilt(b_band, a_band, channel_data)
        
        # Put the sparkling clean data back into the grid
        data[:, col] = channel_data

    crop_amount = 250 #2 sec
    
    # Only crop if the file is actually long enough (e.g., longer than 4 seconds)
    if len(data) > (crop_amount * 2):
        data = data[crop_amount:-crop_amount]

    # 4. Convert the NumPy grid back into a standard Python list 
    # 
    
    print('Finished filtering')
    return data.tolist()


'''
def filter_live_chunk(new_chunk, history_buffer, sampling_rate=125):
    """
    Takes a raw chunk of EEG data, uses a rolling buffer to prevent edge 
    effects, applies 50Hz Notch and 1-50Hz Bandpass filters, and returns 
    the perfectly clean chunk.
    """
    # 1. Add new data to history memory
    history_buffer.extend(new_chunk)
    
    # 2. Keep memory strictly at 600 samples (roughly 5 seconds)
    if len(history_buffer) > 600:
        history_buffer = history_buffer[-600:]
        
    # 3. Convert to NumPy array (BrainFlow requires float64)
    np_buffer = np.array(history_buffer, dtype=np.float64)
    
    # 4. Apply filters to the ENTIRE memory
    DataFilter.perform_bandstop(
        np_buffer, sampling_rate, 48.0, 52.0, 3, FilterTypes.BUTTERWORTH.value, 0
    )
    DataFilter.perform_bandpass(
        np_buffer, sampling_rate, 3.0, 50.0, 4, FilterTypes.BUTTERWORTH.value, 0
    )
    
    # 5. Snip off ONLY the newest chunk
    chunk_length = len(new_chunk)
    clean_chunk = np_buffer[-chunk_length:]
    
    # Return both the clean data AND the updated memory
    return clean_chunk.tolist(), history_buffer
'''
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


