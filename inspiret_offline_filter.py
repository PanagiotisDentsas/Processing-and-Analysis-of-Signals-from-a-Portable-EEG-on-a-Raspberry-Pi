import csv
import numpy as np
from scipy.signal import iirnotch, butter, filtfilt

# ==========================================
# 1. PASTE YOUR EXACT FILTER FUNCTION HERE
# ==========================================
def apply_frequency_filters(number_data):
    """
    Takes raw CSV numbers, applies Notch and Bandpass filters to the EEG columns,
    and returns the cleaned numbers ready to be saved.
    """
    print('Applying filters...')
    
    # Convert the text data into a NumPy grid of numbers
    data = np.array(number_data, dtype=float)

    fs = 125.0              
    notch_freq = 50.0       
    quality_factor = 30.0   
    lowcut = 3.0            # Bumped to 2.0Hz for better sweat/movement blocking
    highcut = 40.0          # Dropped to 40.0Hz to stop fighting the 50Hz Notch
    
    eeg_start_col = 1       
    eeg_end_col = 16        

    nyq = 0.5 * fs 
    
    # Build the filters
    #50hz filter
    b_notch, a_notch = iirnotch(notch_freq, quality_factor, fs)
    
    #non standert 25hz filter
    b_notch25, a_notch25 = iirnotch(w0=25.0, Q=52.0, fs=125)
    
    low = lowcut / nyq
    high = highcut / nyq
    b_band, a_band = butter(6, [low, high], btype='band')

    # Apply the filters
    for col in range(eeg_start_col, eeg_end_col + 1):
        
        channel_data = data[:, col]
        #channel_data = channel_data - np.mean(channel_data)
        
     

        # Scrub it with the 50 Hz Notch filter
        channel_data = filtfilt(b_notch, a_notch, channel_data)
        
        # Scrub it with the 25 Hz Notch filter
        channel_data = filtfilt(b_notch25, a_notch25, channel_data)
        
        # Scrub it with the Bandpass filter
        channel_data = filtfilt(b_band, a_band, channel_data)
       
        data[:, col] = channel_data
        
    crop_amount = 250 
    
    # Only crop if the file is actually long enough (e.g., longer than 4 seconds)
    if len(data) > (crop_amount * 2):
        data = data[crop_amount:-crop_amount]


    print('Finished filtering and croping!')
    return data.tolist()

# ==========================================
# 2. THE FILE MANAGER
# ==========================================
def process_old_file(input_file, output_file):
    print(f"Opening old file: {input_file}")
    
    headers = []
    raw_numbers = []
    
    # Step A: Read the raw CSV
    try:
        with open(input_file, 'r') as infile:
            reader = csv.reader(infile, delimiter=';')
            
            # Grab the very first row (the text headers) and save it for later
            headers = next(reader) 
            
            # Grab all the remaining rows (the actual numbers)
            for row in reader:
                try:
                    # Ensure the row has the correct number of columns before adding
                    if len(row) > 16: 
                        raw_numbers.append(row)
                except Exception:
                    pass
    except FileNotFoundError:
        print(f"❌ Error: Could not find {input_file}. Check the file path!")
        return

    # Step B: Push the numbers through your DSP engine
    clean_numbers = apply_frequency_filters(raw_numbers)

    # Step C: Save everything to a brand new file
    print(f"Saving cleaned data to: {output_file}")
    with open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=';')
        
        # Put the text headers back at the top
        writer.writerow(headers) 
        
        # Write the sparkling clean math underneath
        writer.writerows(clean_numbers)
        
    print("✅ File successfully upgraded!")

# ==========================================
# 3. RUN THE SCRIPT
# ==========================================
if __name__ == "__main__":
    # Just type the session number you want to rescue
    session_num = input("Enter the session number to filter (e.g., 61): ")
    
    base_path = f'/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session{session_num}/'
    
    old_raw_file = base_path + 'openbcirecordings.csv'
    
    # We save it as a NEW file so we never accidentally destroy the original raw data!
    new_clean_file = base_path + 'upgraded_filtered_recordings.csv'
    
    process_old_file(old_raw_file, new_clean_file)
