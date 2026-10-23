import collections, serial, time
import board, busio
import smbus
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15.ads1x15 import Mode
from pyOpenBCI import OpenBCICyton
#from pylsl import StreamInfo, StreamOutlet# DEPRECATED
from brainflow.board_shim import BoardShim, BrainFlowInputParams, LogLevels, BoardIds
import numpy as np

#################################################

# Create bus
global bus, i2c
bus = smbus.SMBus(1)
i2c = busio.I2C(board.SCL, board.SDA)

#################################################

# Call functions for creating all objects
def objects(params):
    
    # Create list of strings for storing warning messages for display
    msg = [] 
    
    # Initialise tuple with objects
    inspire_objects = collections.namedtuple('inspire_objects', 'i2c ads mpu openbci fes clock')
    
    # Create objects
    inspire_objects.ads,msg = obj_ads(params, msg)
    inspire_objects.mpu,msg = obj_mpu(params, msg)
    inspire_objects.openbci,msg = obj_openbci(params, msg)
    inspire_objects.clock,msg = obj_clock(params, msg) #will be left empty, not created due to address conflict
    inspire_objects.fes,msg = obj_fes(params,msg)
        
    # Return output
    return inspire_objects,msg

#################################################

#Create ads objects
def obj_ads(params, msg):
    
    # Create ADS objects and check availability
    ads = [0]*len(params.inaddr.ads_addr.vals)
    not_found = []
    for i in range (len(ads)):
        
        try:
            ads[i] = ADS.ADS1015(i2c,address=params.inaddr.ads_addr.vals[i])
            ads[i].chan_labels = params.inaddr.ads_addr.channels[i]
        except:
            not_found = not_found + [i]
            msg=msg+["Warning: Object '"+params.inaddr.ads_addr.desc[i]+"' in address "+str(hex(params.inaddr.ads_addr.vals[i]))+" cannot be found"]
    
    # Remove undetected objects
    for i in range(len(not_found)-1,-1,-1):
        del ads[not_found[i]]
    
    # Set ADS parameters
    for i in range(len(ads)):
        ads[i].gain = params.exp.ads_gain
        ads[i].data_rate = params.exp.ads_rate
        ads[i].mode = Mode.CONTINUOUS
    
    # Set input channels
    # AnalogIn(ads, ADS.P0, ADS.P1) for differential reading
    pins = [0,1,2,3]
    for i in range(len(ads)):
        ads[i].channels = [0]*4
        for j in range(4):
            ads[i].channels[j] = AnalogIn(ads[i], pins[j])
    
    # Return output
    return ads,msg

#################################################

# Class for IMU object
#   Used by obj_mpu to create IMU object
class MPU_OBJ:
    addr = desc = []
    gyro_sens = accel_sens = []

#################################################

# Create mpu objects
def obj_mpu(params, msg):
            
    # Initialise IMU objects
    mpu = [0]*len(params.inaddr.mpu_addr.vals)
    
    
    # Check sensor availability
    reg_addr = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('PWR_MGMT_1')]
    
    not_found = []
    found = []
    
    for i in range (len(params.inaddr.mpu_addr.vals)):
        mpu[i] = MPU_OBJ()
        try:
            bus.read_byte_data(params.inaddr.mpu_addr.vals[i],reg_addr)
            found = found + [i]
        except:
            not_found = not_found + [i]
            msg=msg+["Warning: Object '"+params.inaddr.mpu_addr.desc[i]+"' in address "\
                     +str(hex(params.inaddr.mpu_addr.vals[i]))+" cannot be found"]
    
    # Perform self-test and create objects for modules with a successful result
    for i in found:
        
        test_fail = False
        #obj_mpu_selftest(params,i2c_address)
                
        if test_fail:
            not_found = not_found + [i]
            #found.remove(i)
            msg=msg+["Warning: Failed self-test for object '"+params.inaddr.mpu_addr.desc[i]\
                     +"' in address "+str(hex(params.inaddr.mpu_addr.vals[i]))]
        else:
            # Create objects
            mpu[i].chan_labels = params.inaddr.mpu_addr.channels[i]
            mpu[i].addr = params.inaddr.mpu_addr.vals[i]
            mpu[i].gyro_sens,mpu[i].accel_sens = MPU6050_start(params,\
                                                               params.inaddr.mpu_addr.vals[i])
        
    # Remove objects that were not detected or failed to pass self-test
    for i in range(len(not_found)-1,-1,-1):
        del mpu[not_found[i]]  
    
    # Return output
    return mpu,msg

#################################################

# Initialisation of a single MPU sensor (accelerometer & gyroscope)
def MPU6050_start(params,addr):
    
    # Set sampling rate
    reg_addr = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('SMPLRT_DIV')]
    bus.write_byte_data(addr, reg_addr, params.exp.smplrt_div)
    time.sleep(0.1)
    
    # Reset all sensors
    reg_addr = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('PWR_MGMT_1')]
    bus.write_byte_data(addr,reg_addr,0x00)
    time.sleep(0.1)
    
    # Power management and crystal settings
    bus.write_byte_data(addr, reg_addr, 0x01)
    time.sleep(0.1)
    
    # Write to Configuration register
    reg_addr = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('CONFIG')]
    bus.write_byte_data(addr, reg_addr, 0)
    time.sleep(0.1)
    
    # Write to Gyro configuration register
    reg_addr = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('GYRO_CONFIG')]
    gyro_config_sel = [0b00000,0b010000,0b10000,0b11000] # byte registers
    gyro_config_vals = [250.0,500.0,1000.0,2000.0] # degrees/sec
    gyro_indx = 0
    bus.write_byte_data(addr, reg_addr, int(gyro_config_sel[gyro_indx]))
    time.sleep(0.1)
    
    # Write to Accel configuration register
    reg_addr = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('ACC_CONFIG')]
    accel_config_sel = [0b00000,0b01000,0b10000,0b11000] # byte registers
    accel_config_vals = [2.0,4.0,8.0,16.0] # g (g = 9.81 m/s^2)
    accel_indx = 0
    bus.write_byte_data(addr, reg_addr, int(accel_config_sel[accel_indx]))
    time.sleep(0.1)
    
    # Interrupt register (related to overflow of data [FIFO])
    reg_addr = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('INT_ENABLE')]
    bus.write_byte_data(addr, reg_addr, 1)
    time.sleep(0.1)
    
    # Return output
    return gyro_config_vals[gyro_indx],accel_config_vals[accel_indx]

#################################################

# Read data from MPU sensor (accelerometer & gyroscope) - Called by mpu6050_conv
def read_raw_bits(addr, reg):
    
    # Read accel and gyro values
    high = bus.read_byte_data(addr, reg)
    low = bus.read_byte_data(addr, reg+1)

    # Combine higha and low for unsigned bit value
    value = ((high << 8) | low)
    
    # Convert to +- value
    if(value > 32768):
        value -= 65536
    
    # Return output
    return value

#################################################

# Read data from MPU sensor (accelerometer & gyroscope) - Called by mpu6050_conv
def mpu6050_conv(obj, params):
    
    # Register addresses (gyro not used)
    reg_addr_x1 = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('ACCEL_XOUT_H')]
    reg_addr_y1 = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('ACCEL_YOUT_H')]
    reg_addr_z1 = params.inaddr.mpu_reg_addr.vals[\
        params.inaddr.mpu_reg_addr.desc.index('ACCEL_ZOUT_H')]
    #reg_addr_x2 = params.inaddr.mpu_reg_addr.vals[\
    #    params.inaddr.mpu_reg_addr.desc.index('GYRO_XOUT_H')]
    #reg_addr_y2 = params.inaddr.mpu_reg_addr.vals[\
    #    params.inaddr.mpu_reg_addr.desc.index('GYRO_YOUT_H')]
    #reg_addr_z2 = params.inaddr.mpu_reg_addr.vals[\
    #    params.inaddr.mpu_reg_addr.desc.index('GYRO_ZOUT_H')]
        
    # Raw acceleration bits
    acc_x = read_raw_bits(obj.addr,reg_addr_x1)
    acc_y = read_raw_bits(obj.addr,reg_addr_y1)
    acc_z = read_raw_bits(obj.addr,reg_addr_z1)

    # Raw gyroscope bits (gyro not used)
    #gyro_x = read_raw_bits(obj.addr,reg_addr_x2)
    #gyro_y = read_raw_bits(obj.addr,reg_addr_y2)
    #gyro_z = read_raw_bits(obj.addr,reg_addr_z2)
    
    # Raw temperature bits (temperature measurement not used)
    #t_val = read_raw_bits(TEMP_OUT_H)

    # Convert to acceleration in g
    a_x = (acc_x/(2.0**15.0))*obj.accel_sens
    a_y = (acc_y/(2.0**15.0))*obj.accel_sens
    a_z = (acc_z/(2.0**15.0))*obj.accel_sens
    
    # Convert to gyro dps (gyro not used)
    #w_x = (gyro_x/(2.0**15.0))*obj.gyro_sens
    #w_y = (gyro_y/(2.0**15.0))*obj.gyro_sens
    #w_z = (gyro_z/(2.0**15.0))*obj.gyro_sens
    
    # Convert to temperature measurement (not used)
    #temp = ((t_val)/333.87)+21.0
    
    # Store values in single list
    chan_vals = [a_x, a_y, a_z]
    
    # Return output
    return chan_vals

#################################################

# Perform a self-test on MPU9050
def obj_mpu_selftest(params,i2c_address):
    
    # Set digital low pass filter (DLPF) to 2 for registers
    # -26 (CONFIG)
    # -29 (ACCEL_CONFIG 2)
    dlfp = 2
    
    # Set full scale range for registers
    # -27 (GYRO_CONFIG): 250dps
    #-28 (ACCEL_CONFIG): 2g
    acc_fs_sel = 00
    
    # Set sampling rate to 1kHz
    
    # Average 200 readings for gyro & acc
    # The averaged values will be the LSB of:
    # GX_OS, GY_OS, GZ_OS, AX_OS, AY_OS, AZ_OS
    
    # Set USR_Reg: (1Bh) Gyro_Config, gdrive_axisCTST [0-2] to b111 to enable Self-Test
    
    # Set USR_Reg: (1Ch) Accel_Config, AX/Y/Z_ST_EN [0-2] to b111 to enable Self-Test
    
    time.sleep(0.02)
    
    # Read & average values again
    
    # Calculate response
    #mpu = [0]*3
    #return mpu,msg

#################################################

# Class for OpenBCI object (DEPRECATED)
class OPENBCI_OBJ:
    obj = chan_labels = []

#################################################

#Functions for streaming OpenBCI data (DEPRECATED)
def lsl_streamers(sample):
    global eeg, aux
    eeg = np.array(sample.channels_data)
    aux = np.array(sample.aux_data)

def board_stream(board_bci):
    board_bci.start_stream(lsl_streamers)

#################################################

# Create OpenBCI EEG object
def obj_openbci(params, msg):
    
    # Set logging
    #BoardShim.set_log_file(params.config.logfile)
    BoardShim.disable_board_logger()
    
    # Set BrainFlow arguments
    board_pars = BrainFlowInputParams()
    board_pars.timeout = params.exp.markiv_timeout
    board_pars.file = params.exp.markiv_file
    board_pars.serial_port = params.inaddr.eeg
    board_id = params.inaddr.eeg_board_id
    
    # Initialise object
    board = BoardShim(board_id, board_pars)
    
    # Get board info
    #  - accel_channels      / BoardShim.get_accel_channels(board_id)
    #  - analog_channels     / BoardShim.get_analog_channels(board_id)
    #  - ecg_channels
    #  - eeg_channels        / BoardShim.get_eeg_channels(board_id)
    #  - eeg_names           / BoardShim.get_eeg_names(board_id)
    #  - emg_channels
    #  - eog_channels
    #  - marker_channel      / BoardShim.get_marker_channel(board_id)
    #  - name                / BoardShim.get_device_name(board_id)
    #  - num_rows            / BoardShim.get_num_rows(board_id)
    #  - other_channels      / BoardShim.get_other_channels(board_id)
    #  - package_num_channel / BoardShim.get_package_num_channel(board_id)
    #  - sampling_rate       / BoardShim.get_sampling_rate(board_id)
    #  - timestamp_channel   / BoardShim.get_timestamp_channel(board_id)
    board.info = board.get_board_descr(board_id)
    #board.info.keys()
    
    
    # Delete reduntant fields
    redundant_fields = ["ecg_channels","emg_channels","eog_channels"]
    for field in redundant_fields:
        del board.info[field]
    
    # Prepare session
    try:
        board.prepare_session()
    except Exception as e:
        msg=msg+["Warning - Unable to establish OpenBCI connection ('" + params.inaddr.eeg + "')"]
        msg=msg+[" -" + str(e)]
        board = []        
    
    # Return output
    return board,msg

# DEPRECATED
def obj_openbci2(params, msg):
    
    openbci = [OPENBCI_OBJ()]
    try:
        openbci[0].obj = OpenBCICyton(port=params.inaddr.eeg, daisy=True)
        openbci[0].chan_labels = params.inaddr.eeg_channels
        found = True
    except:
        msg=msg+["Warning: OpenBCI Dongle not found in '" + params.inaddr.eeg + "'"]
        openbci = []
        found = False
        
    #Check connectivity
    if found:
        try:
            openbci_port = openbci[0].obj.find_port()
        except:
            msg=msg+["Warning: OpenBCI Recording device not found"]
            openbci = []
            found = False
    
    if found:
        # Declare Mark IV data stream
        info_eeg = StreamInfo('OpenBCIEEG', 'EEG', \
                              params.exp.markiv_eeg_chans, params.exp.markiv_frate, \
                              'float32', 'OpenBCIEEG')
        outlet_eeg = StreamOutlet(info_eeg)
        
        # Declare Accelerometer data stream
        info_aux = StreamInfo('OpenBCIAUX', 'AUX', \
                              params.exp.markiv_aux_chans, params.exp.markiv_frate, \
                              'float32', 'OpenBCIAUX')
        outlet_aux = StreamOutlet(info_aux)
    
    # Return output
    return openbci,msg

#################################################

# Create FES object
def obj_fes(params, msg):
    
    error = False
    try:
        fes_out = serial.Serial(port=params.outaddr.fes, baudrate=params.exp.fes_baudrate,
                                bytesize=params.exp.fes_bytesize, parity=params.exp.fes_parity,
                                stopbits=params.exp.fes_stopbits,
                                timeout=params.exp.fes_timeout,
                                write_timeout=params.exp.fes_write_timeout,
                                xonxoff=params.exp.fes_xonxoff,
                                rtscts=params.exp.fes_rtscts, dsrdtr=params.exp.fes_dsrdtr)
    except:
        fes_out =[]
        msg=msg+["Warning: Object 'FES' not connected in port '"+params.outaddr.fes+"'"]
    
    if fes_out != []:
        fes_out.flush()
        fes_out.write([0xc0])
        time.sleep(0.05) # Delay is necessary, or else read will return nothing
        response = fes_out.read()
        #print(response)
        if response != b'\x81':
            fes_out =[]
            msg=msg+["Warning: Object 'FES' in port '"+params.outaddr.fes+"' has not acknowledged connection"]
    
    # Return output
    return fes_out,msg

#################################################

# Create clock object (not used due to address conflict with MPU)
def obj_clock(params, msg):
    clock = []
    
    # Return output
    return clock, msg

#################################################

# Define data headers
def data_headers(objects,pars):
    
    # GPIO data headers
    ads_count = len(objects.ads)
    mpu_count = len(objects.mpu)
    if mpu_count + ads_count != 0:
        gpiodata = ["inc","timestamp"]
        for i in range(ads_count):
            gpiodata += objects.ads[i].chan_labels
        for i in range(mpu_count):
            gpiodata += objects.mpu[i].chan_labels
        
    else:
        gpiodata = []
    #gpiodata = [gpiodata]
    
    # OpenBCI board data headers
    if objects.openbci != []:
        boarddata = ["inc"]+[objects.openbci.info["eeg_names"]]+pars.inaddr.eeg_extra_channels
        # \
                    # ["Accel_x","Accel_y","Accel_z"]+\
                    # ["Unknown","D11_dig","D12_dig","D13_dig","D12_anmode","D17","D18",
                     # "D11_ana","D12_ana","D13_ana"]+\
                    # ["timestamp","marker"]
    else:
        boarddata = []
    #boarddata = [boarddata]
    
    # Return output
    return gpiodata,boarddata
