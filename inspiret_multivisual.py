import csv
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURATION ---
num_samples_to_plot = 200  # 4 seconds of data (125Hz). Change this to see more/less time!
num_channels = 16

print("--- INSPiRE 16-Channel Time Domain Visualizer ---")
session_num = input("Enter session number : ")

base_path = f'/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session{session_num}/'
raw_filepath = base_path + 'openbcirecordings.csv'
filt_filepath = base_path + 'filteredopenbcirecordings.csv'
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
                    pass
    except FileNotFoundError:
        print(f"❌ Error: Could not find file -> {filename}")
        return None
    return np.array(data)

# --- 1. Load the Data ---
print("Loading all 16 channels of data...")
raw_data = load_all_channels(raw_filepath)
filt_data = load_all_channels(filt_filepath)

if raw_data is not None and filt_data is not None:
    print("Drawing massive 16-row graph... (this might take a second)")
    
    # --- 2. Create the 16-Row Figure ---
    # figsize=(15, 12) makes a tall window so the rows aren't squished
    fig, axes = plt.subplots(num_channels, 1, figsize=(15, 12), sharex=True)
    fig.suptitle(f"Time Domain: Raw vs Filtered - All 16 Channels (First {num_samples_to_plot} samples)", fontsize=16)

    # --- 3. Loop through and draw each row ---
    for i in range(num_channels):
        # Extract just the chunk of time we want to look at
        raw_ch = raw_data[:num_samples_to_plot, i]
        filt_ch = filt_data[:num_samples_to_plot, i]
        
        # Plot Red (Raw) behind Blue (Filtered)
        axes[i].plot(raw_ch, color='red', alpha=0.5, linewidth=1)
        axes[i].plot(filt_ch, color='blue', linewidth=1.5)
        
        # Format each row to look clean
        axes[i].set_ylabel(f"Ch {i+1}", rotation=0, labelpad=25, verticalalignment='center', fontweight='bold')
        axes[i].grid(True, alpha=0.3)
        axes[i].set_yticks([]) # Hide the messy voltage numbers on the side

    # Put the time label only on the absolute bottom graph
    axes[-1].set_xlabel("Samples (Time)")
    
    # --- 4. Add a Master Legend at the top ---
    from matplotlib.lines import Line2D
    custom_lines = [Line2D([0], [0], color='red', alpha=0.5, lw=2),
                    Line2D([0], [0], color='blue', lw=2)]
    fig.legend(custom_lines, ['Raw Data (Fuzzy)', 'Filtered Data (Clean)'], loc='upper right')

    # This squeezes the rows together perfectly so they fit the window
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, hspace=0.1) 
    plt.show()
