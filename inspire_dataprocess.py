# Import modules
from datetime import datetime
import os, csv, time, numpy as np
import inspire_interface, inspire_objects, inspire_datarecord
from inspire_filters import filter_live_chunk
from inspire_features import extract_band_power
from inspire_utils import print_performance
from gpiozero import LED

# Tell Python we plugged the LED into GPIO Pin 17
wheelchair_signal = LED(17)
#################################################

# Handle real-time processing
# Note: Use 1st command for threading, 2nd for multiprocessing
def data_process(objects, pars, process, feedback, task_type, guide,filt,shared_powers):
#def data_process(objects, channels, pars, process, task_type, guide, conn):
    
    # Define global variable
    global gpiodata
    
    if task_type == 1:
        
        # Gait thresholds
        states = pars.process.gait_states
        sensor_thres = pars.process.thresholds_gait
        eeg_thres = pars.process.thresholds_eeg
        emg_thres = pars.process.thresholds_emg
        gait_thres = [emg_thres[0],emg_thres[1],emg_thres[0],emg_thres[1],
                      sensor_thres[1],sensor_thres[0],sensor_thres[1],sensor_thres[0],
                      sensor_thres[2],sensor_thres[2],
                      sensor_thres[3],sensor_thres[4],0,
                      sensor_thres[3],sensor_thres[4],0]
        
        # FES parameters
        channel_mode = pars.process.channel_mode
        pulse_width = pars.process.fes_pulse_width
        current = pars.process.fes_current
        serial = objects.fes
        
        # Wait for data recording to begin
        time.sleep(2)
        
        # Begin time monitoring (to avoid continuous output commands)
        start=time.time()
        
        while inspire_datarecord.recording:
        
            # Get latest measurements
            # Last 10 GPIO inputs
            # Last 130 OpenBCI measurements
            #print(inspire_datarecord.gpiodata[-11:-1])
            gpio = np.mean(np.delete(np.array(inspire_datarecord.gpiodata[-11:-1]),[0,1],1),axis = 0)
            #eeg_data = objects.openbci.get_current_board_data(130)
            #objects.openbci.insert_marker(1) #insert integer as a marker
            
            # State Classification
            thres_comp =np.sign(np.subtract(gpio[4:8],gait_thres[4:8])) #comparison with thresholds
#             if thres_comp == [1,1,1,1]: #stance
#                 channels = []
#             elif thres_comp == [-1,-1,1,1]: #midstance_l
#                 channels = [3,4]
#             elif thres_comp == [1,-1,-1,1]: #heelstrike_r
#                 channels = [3]
#             elif thres_comp == [1,1,-1,1]: #toeoff_l
#                 channels = [1,2,4]
#             elif thres_comp == [1,1,-1,-1]: #midstance_r
#                 channels = [1,2]
#             elif thres_comp == [-1,1,1,-1]: #heelstrike_l
#                 channels = [1]
#             elif thres_comp == [-1,1,1,1]: #toeoff_r
#                 channels = [2,3,4]
#             else:
#                 channels = []
            
            if thres_comp[0]==-1 & thres_comp[1]==-1: #midstance_l
                channels = [3,4]
            elif thres_comp[1]==-1 & thres_comp[2]==-1: #heelstrike_r
                channels = [3]
            elif thres_comp[2]==-1 & thres_comp[1]==1 & thres_comp[3]==1: #toeoff_l
                channels = [1,2,4]
            elif thres_comp[2]==-1 & thres_comp[3]==-1: #midstance_r
                channels = [1,2]
            elif thres_comp[0]==-1 & thres_comp[3]==-1: #heelstrike_l
                channels = [1]
            elif thres_comp[0]==-1 & thres_comp[1]==1 & thres_comp[3]==1: #toeoff_r
                channels = [2,3,4]
            else:
                channels = []
            
            # Send command to FES
            if time.time()-start > 3:
                for c in channels:
                    fes_send(serial,channel_mode,pulse_width,current,c)
                start=time.time()            
            
    elif task_type == 2:
        # Wheelchair parameters
    
        # Create the memory variable right before the loop starts
        my_history_buffer = []    
        while inspire_datarecord.recording:
        # 1. Grab raw data from the headset
            raw_data = objects.openbci.get_current_board_data(130)
            
            # --- THE GATEKEEPER ---
            # ONLY do math if we actually have a full 130 samples!
            if raw_data.shape[1] >= 130:
                start_time = time.perf_counter()
                
                # 2. Clean it perfectly using your live filter      
                
                if filt == True:
                    # Clean the data and update memory
                    clean_data, my_history_buffer = filter_live_chunk(raw_data[1], my_history_buffer)
                    
                else:
                    # Bypass the filter entirely! 
                    # Just grab the raw fuzzy data and pass it forward.
                    clean_data = raw_data[1]
                                                 

                # 3. Extract features one at a time
                theta_power = extract_band_power(clean_data, 5.0, 8.0)
                beta_power = extract_band_power(clean_data, 12.0, 25.0)
                
                ###set the perameters to tranfer them and then display them###
                shared_powers["theta"] = theta_power
                shared_powers["beta"] = beta_power
                
                ############################visualization
                
                
               
                try:
                    # 1. Calculate the total combined energy of both bands
                    total_power = theta_power + beta_power
                    
                    # 2. Prevent "Divide by Zero" if the headset disconnects
                    if total_power > 0:
                        theta_percent = (theta_power / total_power) * 100
                        beta_percent = (beta_power / total_power) * 100
                    else:
                        theta_percent = 0
                        beta_percent = 0
                    
                    # 3. Apply the Percentages to the Bar Heights
                    inspire_interface.bars[0].set_height(theta_percent)
                    inspire_interface.bars[1].set_height(beta_percent)
                    
                    # 4. Show the RAW data in the text labels so you still know the absolute strength
                    inspire_interface.theta_text.set_text(f"{theta_power:.1f}")
                    inspire_interface.beta_text.set_text(f"{beta_power:.1f}")
                    
                except Exception as e:
                    print(f"⚠️ UI Update Error: {e}")
                # -----------------------------------------
                   
                   
                   
                
                print(f"Theta: {theta_power:.2f} | Beta: {beta_power:.2f}")
                
                #############################################
                # 4. Function for output (Wheelchair decision)
                    
                    # If Theta is double Beta, output = 1. Otherwise, 0.
                if theta_power > (beta_power * 2):
                    command = 1
                else:
                    command = 0
                    
                # Send the command using your consistent function structure
                wheelchair_send(command, wheelchair_signal)
                ############################################################
                
                
                #checking the systems perfomance   
                delay, cpu,temp = print_performance(start_time)
                time.sleep(0.5)
            else:
                # If we have less than 130 samples, just wait 10 milliseconds and check again
                time.sleep(0.01)
        
        

#################################################Choice outputs
        
# Send command to FES device
def fes_send(serial,channel_mode,pulse_width,current,channel_num):
    
    # Calculate checksum
    checksum = (channel_num-1+pulse_width+current) % 32
    
    # Convert to binary
    channel_mode_bin = format(channel_mode, '#04b')[2:4]
    channel_num_bin = format(channel_num-1, '#05b')[2:5]
    pulse_width_bin = format(pulse_width, '#011b')[2:11]
    current_bin = format(current, '#09b')[2:9]
    checksum_bin = format(checksum, '#07b')[2:7]
    
    # Command bytes
    command_bytes = []
    command_bytes += ['1' + channel_mode_bin + checksum_bin]
    command_bytes +=  ['0' + channel_num_bin + '00' + pulse_width_bin[0:2]]
    command_bytes +=  ['0' + pulse_width_bin[2:11]]
    command_bytes +=  ['0' + current_bin]
    
    # Convert to integer
    fes_command=[]
    for b in command_bytes:
        fes_command += [int(b,2)]
    
    # Send command to device
    serial.write(fes_command)

#FOR DISPLAY PURPOSES after run:
#import inspire_dataprocess
#inspire_dataprocess.fes_send(objects.fes,pars.process.channel_mode,pars.process.fes_pulse_width,pars.process.fes_current,1)

def wheelchair_send(drive_command, pin_object):
    """
    Sends a command to the wheelchair motor controller (or LED).
    drive_command: 1 (Drive/ON) or 0 (Stop/OFF)
    """
    # 1. Log the command (optional, but great for debugging)
    # print(f"Sending Wheelchair Command: {drive_command}")
    
    # 2. Execute the hardware output
    if drive_command == 1:
        
        print('Power on')
        pin_object.on()   # Turn pin HIGH (3.3V)
    else:
        print('Power off')
        pin_object.off()  # Turn pin LOW (0V)
        
        
###############################################
