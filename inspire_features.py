import numpy as np
from brainflow.data_filter import DataFilter, WindowOperations

def extract_band_power(clean_chunk, f_min, f_max, sampling_rate=125):
    """
    Takes a clean chunk of EEG data and extracts the power of 
    a specific frequency band defined by f_min and f_max.
    """
    # 1. Convert to BrainFlow's required format
    data_array = np.array(clean_chunk, dtype=np.float64)
    
    # 2. Setup FFT parameters for a 130-sample chunk
    nfft = 128 
    overlap = 64 
    
    try:
        # 3. Calculate Power Spectral Density (Welch's Method)
        psd = DataFilter.get_psd_welch(
            data_array, 
            nfft, 
            overlap, 
            int(sampling_rate), # <--- THE FIX: Force it to be a pure integer
            WindowOperations.HANNING.value
        )
        
        # 4. Extract your requested frequency band
        power = DataFilter.get_band_power(psd, float(f_min), float(f_max))
        
        return power
        
    except Exception as e:
        print(f"Feature Extraction Error: {e}")
        return 0.0
