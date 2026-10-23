import csv
import matplotlib.pyplot as plt

# --- 1. THE FUNCTION DEFINITION ---
def get_channel_data(filename, channel_index):
    data = []
    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader) 
        for row in reader:
            try:
                data.append(float(row[channel_index]))
            except ValueError:
                pass
    return data

# --- 2. THE SCRIPT ---
print("Loading data...")
'''
raw_path = '/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session28/openbcirecordings.csv'
filt_path = '/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session28/filteredopenbcirecordings.csv'
'''

print("--- INSPiRE 16-Channel Time Domain Visualizer ---")
session_num = input("Enter session number : ")

base_path = f'/home/raspberry/Desktop/Documents/INSPiRE/Data/panagiotis/session{session_num}/'
raw_path = base_path + 'openbcirecordings.csv'
filt_path = base_path + 'filteredopenbcirecordings.csv'



raw_fp1 = get_channel_data(raw_path, 1)
filt_fp1 = get_channel_data(filt_path, 1)

print("Drawing graph...")
plt.figure(figsize=(12, 6))

plt.plot(raw_fp1[:500], label='Raw Data (Fuzzy)', color='red', alpha=0.5, linewidth=1)
plt.plot(filt_fp1[:500], label='Filtered Data (Smooth)', color='blue', linewidth=2)

plt.title("Filter Verification: Fp1 Channel")
plt.xlabel("Samples")
plt.ylabel("Voltage")
plt.legend()
plt.grid(True)
plt.show()
