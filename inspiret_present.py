import csv
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
from matplotlib.ticker import LinearLocator, FormatStrFormatter

# --- CONFIGURATION ---
window_size = 500  # How many samples to show on screen at once (4 seconds at 125Hz)
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
filt_data = load_all_channels(filt_filepath)

if filt_data is not None:
    total_samples = len(filt_data)
    print(f"Drawing massive 16-row graph with {total_samples} samples... (this might take a second)")
    
    # --- 2. Create the 16-Row Figure ---
    # sharex=True means if we scroll one graph, they all scroll perfectly together
    fig, axes = plt.subplots(num_channels, 1, figsize=(15, 12), sharex=True)
    fig.suptitle(f"Time Domain: Filtered Data - All 16 Channels", fontsize=16)

    # --- 3. Loop through and draw EVERY sample for each row ---
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
    
    # Set the initial view to just the first 'window_size' samples
    axes[0].set_xlim(0, window_size)

    # --- 4. Add the Interactive Scrollbar (Slider) ---
    # Make room at the bottom of the window for the slider
    plt.subplots_adjust(top=0.93, bottom=0.15, hspace=0.25) 
    
    # Create an axis area specifically for the slider
    ax_slider = plt.axes([0.15, 0.05, 0.7, 0.03])
    
    # Create the slider object (starts at 0, goes up to the end minus the window size)
    time_slider = Slider(
        ax=ax_slider,
        label='Scroll Time ',
        valmin=0,
        valmax=max(0, total_samples - window_size),
        valinit=0,
        valstep=10  # Jump by 10 samples for smoother scrolling
    )

    # Function that runs whenever you drag the slider
    def update_window(val):
        start_point = int(time_slider.val)
        # Because we used sharex=True, we only need to update the x-axis on the first plot
        axes[0].set_xlim(start_point, start_point + window_size)
        fig.canvas.draw_idle()

    # Link the slider to the update function
    time_slider.on_changed(update_window)

    # Add a Master Legend
    from matplotlib.lines import Line2D
    custom_lines = [Line2D([0], [0], color='blue', lw=2)]
    fig.legend(custom_lines, ['Filtered Data (Clean)'], loc='upper right')

    plt.show()
