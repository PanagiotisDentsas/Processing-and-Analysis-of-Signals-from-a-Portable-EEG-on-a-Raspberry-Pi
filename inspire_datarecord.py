# Import modules
from datetime import datetime
import os, csv, time
import inspire_interface, inspire_objects


#################################################

# Handle real-time recording (DEPRECATED)
def record2(objects,channels, pars, process):
    global data
    
    data = [["inc","timestamp"] + channels.labels] # + [[0]*len(channels["labels"])]
    inc = 0
    
    # Fetch preprocess parameters
    force_scalein = pars.preprocess.force_scalein
    force_scaleout = pars.preprocess.force_scaleout
    flex_scalein = pars.preprocess.flex_scalein
    flex_scaleout = pars.preprocess.flex_scaleout    
    
    # Start Recording
    print("Recording started")
    while recording:
        
        # Initialise vector
        #m = [0]*len(channels.ads['labels'])
        m= []
        
        # Get measurements
        for i in range(len(channels.ads['labels'])):
            
            #m[i] = channels.ads['obj'][i].voltage
            m = m + [channels.ads['obj'][i].voltage]
            
            # Rescale inputs
            if 'Force' in channels.ads['labels'][i]:
                m[i] = force_scaleout[0] + (m[i]-force_scalein[0])*force_scaleout[1]/\
                    (force_scalein[1]-force_scalein[0])
            elif 'Flex' in channels.ads['labels'][i]:
                m[i] = flex_scaleout[0] + (m[i]-flex_scalein[0])*flex_scaleout[1]/\
                    (flex_scalein[1]-flex_scalein[0])
        
        for i in range(len(objects.mpu)):
            #print(m)
            #print(inspire_objects.mpu6050_conv(objects.mpu[i],pars))
            m=m+inspire_objects.mpu6050_conv(objects.mpu[i],pars)
        
        #print(m)
                
        # Update feedback display
        for i in range(len(inspire_interface.bars)):
           inspire_interface.bars[i].set_height(m[i])
        
        #
        if any(channels.openbci['labels']):
            a = inspire_objects.eeg*pars.exp.markiv_eeg_scale
            b = inspire_objects.aux*pars.exp.markiv_aux_scale            
            m = m + a.tolist() + b.tolist()
        
        # Append values to data table
        data=data+[[inc,datetime.now()]+m]
        inc = inc+1
    return

#################################################

# Handle real-time recording
# Note: Use 1st command for recording variable for threading, 2nd for multiprocessing
def record(objects, pars, process):
#def record(objects, pars, process, conn):
    
    # Define global variable
    global gpiodata
    global boarddata
    
    # Fetch preprocess parameters
    force_scalein = pars.preprocess.force_scalein
    force_scaleout = pars.preprocess.force_scaleout
    flex_scalein = pars.preprocess.flex_scalein
    flex_scaleout = pars.preprocess.flex_scaleout 
    
    # Begin openbci recording
    if objects.openbci != []:
        objects.openbci.start_stream(num_samples = pars.exp.markiv_num_samples, \
                           streamer_params="file://" + pars.config.openbcidatafile + ":w")
    #time.sleep(0.5)
    
    # GPIO recording initialisation
    gpiodata = []
    inc = -1   
    ads_num = len(objects.ads)
    mpu_num = len(objects.mpu)
    
    # Start GPIO Recording
    print("Recording started")
    while recording: #This for threading, use the below command for multiprocessing
    #while recording.value:
    #while inc<=1000: #for testing
        
        # Initialise vector
        inc+=1
        m = [inc,datetime.now()]
        
        # Get ADS data
        for i in range(ads_num):
            for j in range(len(objects.ads[i].channels)):
                m += [objects.ads[i].channels[j].voltage]
        
        # Rescale inputs
            if 'Force' in objects.ads[i].chan_labels:
                m[i] = force_scaleout[0] + (m[i]-force_scalein[0])*force_scaleout[1]/\
                   (force_scalein[1]-force_scalein[0])
            elif 'Flex' in objects.ads[i].chan_labels:
                m[i] = flex_scaleout[0] + (m[i]-flex_scalein[0])*flex_scaleout[1]/\
                       (flex_scalein[1]-flex_scalein[0])
        
        # Get IMU data
        for i in range(len(objects.mpu)):
            m += inspire_objects.mpu6050_conv(objects.mpu[i],pars)
                       
        # Get OpenBCI data
        #print(objects.openbci.get_current_board_data(1)) #print last n measurements
        #objects.openbci.insert_marker(1) #insert integer as a marker
        #print(m)
        
        # Send data to connection (only if multiprocessing is used)
        #conn.send(m)
        
        # Append data to accumulating variable for storage
        gpiodata += [m]
        '''
        # Update feedback display
        
        for i in range(len(inspire_interface.bars)):
            inspire_interface.bars[i].set_height(m[i+2])
        '''
    #Send data through the connection (only for multiprocessing)
    #conn.close
    #conn.send(None)
    #conn.send(gpiodata)
    #conn.close (HERE OR 2 LINES ABOVE?)
    
    # Test variable content
    #print(gpiodata)
    return

#################################################

# Create output file with session data
def save_sessiondata(pars,objects,gpiodata):
    #print(gpiodata)
    # Save GPIO data
    with open(pars.config.gpiodatafile,'w') as f:
        write = csv.writer(f,delimiter = ";")
        write.writerow(pars.session.gpio_headers)
        write.writerows(gpiodata)
        f.close
    print("GPIO data saved in" + pars.config.gpiodatafile)
    
    # Add headers to OpenBCI data file
    if objects.openbci!=[]:
        with open(pars.config.openbcidatafile,'r') as f:
            read = csv.reader(f,delimiter = "\t")
            lines = list(read)
        flat_headers = []
        for item in pars.session.openbci_headers:
            flat_headers.extend(str(item).split(','))
        lines.insert(0, flat_headers) #lines.insert(0,pars.session.openbci_headers) change the , to ;
    
        with open(pars.config.openbcidatafile,'w') as f:
            write = csv.writer(f,delimiter = ";")
            write.writerows(lines)
            f.close
        print("OpenBCI data saved in" + pars.config.openbcidatafile)
    else:
        print("OpenBCI data not saved (no stream available)")

'''
# Create output file for the  with session  filtered data
def save_filteredeegdata(pars,objects,gpiodata):
   
    # Add headers to OpenBCI data file
    import inspire_filters
    if objects.openbci!=[]:
        with open(pars.config.openbcidatafile,'r') as f:
            read = csv.reader(f,delimiter = ";")
            lines = list(read)
        inspire_filters   
    
        with open(pars.config.fopenbcidatafile,'w') as f:
            write = csv.writer(f,delimiter = ";")
            write.writerows(lines)
            f.close
        print("OpenBCI filtered data saved in" + pars.config.fopenbcidatafile)
    else:
        print("OpenBCI filtered data not saved (no stream available)")
'''

# Create output file with session filtered data
def save_filteredeegdata(pars, objects, gpiodata):
   
    import inspire_filters
    import csv 
    
    if objects.openbci != []:
        # --- PHASE 1: Extract Pure Numbers ---
        with open(pars.config.openbcidatafile, 'r') as f:
            read = csv.reader(f, delimiter=";")
            lines = list(read)
            
        headers = lines[0]        
        raw_numbers = lines[1:]   
        
        # --- PHASE 2: Apply the Filter ---
        filtered_numbers = inspire_filters.apply_frequency_filters(raw_numbers)
        
        # --- PHASE 3: Rejoin the Headers and Data ---
        final_lines = [headers] + filtered_numbers
        
        # --- PHASE 4: Save to the new file ---
        with open(pars.config.fopenbcidatafile, 'w') as f:
            write = csv.writer(f, delimiter=";")
            write.writerows(final_lines)
            
        print("OpenBCI filtered data saved in " + pars.config.fopenbcidatafile)
        
    else:
        print("OpenBCI filtered data not saved (no stream available)")
