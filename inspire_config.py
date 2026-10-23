# Import modules
import os,collections,sys,serial

#################################################

# Call functions to define all parameters
def params(participant,exp_time,save_data,scale,guide,process,task_type):
    
    inspire_pars = collections.namedtuple('inspire_pars', \
        ['config','inaddr','outaddr','exp',
         'preprocess','featextract','process','feedback','protocol','session','guide'])
    
    inspire_pars.config = config_params(participant)
    inspire_pars.inaddr = i2c_addr_in()
    inspire_pars.outaddr = out_addr()
    inspire_pars.exp = exp_params()
    inspire_pars.preprocess = preprocess_params()
    inspire_pars.featextract = feature_params()
    inspire_pars.process = process_params()
    inspire_pars.feedback = feedback_params()
    inspire_pars.protocol = protocol_stimuli(task_type)
    
    inspire_pars.session = collections.namedtuple('session',\
        ['participant','exp_time','scale','process','task_type',
         'gpio_headers','openbci_headers'])
    inspire_pars.session.participant = participant
    inspire_pars.session.exp_time = exp_time
    inspire_pars.session.scale = scale
    inspire_pars.session.process = process
    inspire_pars.session.guide = guide
    inspire_pars.session.task_type = 'walking' if task_type == 1 else 'wheelchair'
    
    # Return output
    return inspire_pars

#################################################

# Configuration parameters (directories & interfacing)
def config_params(participant):
    
    config = collections.namedtuple('config',
        ['sessionfolder','genpath','folderout','datafile',
         'sessionfile','original_stdout',
         'gui_title','gui_width','gui_height',
         'gui_font','gui_fontsize',
         'gui_fontbgr','gui_fontcolor','gui_startpos','fopenbcidatafile'])
    
    # Data output
    config.original_stdout = sys.stdout # Save a reference to the original standard output
    config.genpath = "/home/raspberry/Desktop/Documents/INSPiRE/Data" # General path
    config.subjectfolder = config.genpath + "/" + participant
    
    gpiodatafile = "gpiorecordings.csv" # Output file for recordings
    openbcidatafile = "openbcirecordings.csv" # Output file for recordings
    fopenbcidatafile = "filteredopenbcirecordings.csv" # Output file for recordings
    sessionfile = "sessiondata.csv" # Output file for session variables
    logfile = "logfile.txt" # Output logfile
    
    config.sessionfolder,config.gpiodatafile,config.openbcidatafile,\
                                config.sessionfile,config.logfile = \
        output_dirs(config.genpath,config.subjectfolder,\
                    gpiodatafile,openbcidatafile,sessionfile,logfile)
    config.fopenbcidatafile = config.sessionfolder + "/" + fopenbcidatafile
    # Interfacing
    config.gui_title, config.gui_width, config.gui_height  = "INSPiRE", 800, 500
    config.gui_font, config.gui_fontsize = 'freesansbold.ttf', 15
    config.gui_fontbgr, config.gui_fontcolor = [0, 0, 0], [255, 255, 255]
    config.gui_startpos = [10,10]
    config.fig_size, config.fig_dpi = [4, 4], 60
    config.ylim_min , config.ylim_max = -0.2, 3.5
    
    # Return output
    return config

#################################################

# Define output folder & files

def output_dirs(genpath, subjectfolder, gpiodatafile, openbcidatafile, sessionfile, logfile):
    
    # Create folder for subject if needed
    if not os.path.exists(genpath):
        os.mkdir(genpath)
        os.mkdir(subjectfolder)
    else:
        if not os.path.exists(subjectfolder): 
            os.mkdir(subjectfolder)
        
    #Create folder for session
    folders = os.listdir(subjectfolder)
    existing_folders = len([s for s in folders if any("session" in s for s in folders)])
    sessionfolder = subjectfolder + "/session" + str(existing_folders+1)
    os.mkdir(sessionfolder)
    
    # Set full filenames
    gpiodatafile = sessionfolder + "/" + gpiodatafile
    openbcidatafile = sessionfolder + "/" + openbcidatafile
    sessionfile = sessionfolder + "/" + sessionfile
    logfile = sessionfolder + "/" + logfile
        
    # Return output
    return sessionfolder,gpiodatafile,openbcidatafile,sessionfile,logfile

#################################################

# Input addresses
def i2c_addr_in():
    
    in_addresses = collections.namedtuple('in_addresses', 'ads_addr mpu_addr mpu_reg_addr clock_addr')
    
    # Input module channels for A/D Converters
    in_addresses.ads_addr = collections.namedtuple('ads_addr', 'desc vals channels')
    in_addresses.ads_addr.desc = ["ADS1: 4 Myoware sensors",
                                  "ADS2: 4 Pressure sensors",
                                  "ADS3: 2 ECG & 2 Flex sensors",
                                  "ADS4: FES input channels"
                                  ]
    in_addresses.ads_addr.vals = [0x48, 0x49, 0x4b, 0x4a]
    in_addresses.ads_addr.channels = [["Myoware 1", "Myoware 2", "Myoware 3", "Myoware 4"],
                                      ["Force_Toe_R","Force_Heel_R","Force_Toe_L","Force_Heel_L"],
                                      ["Flex_Knee_R","Flex_Knee_L","Pulse","ECG"],
                                      ["FES_1_R","FES_2_R","FES_1_L","FES_2_L"]
                                      ]
    
    # Input module channels for IMUs
    in_addresses.mpu_addr = collections.namedtuple('mpu_addr','desc vals')
    in_addresses.mpu_addr.desc = ["IMU1: Right Leg",
                               "IMU2: Left Leg"
                               ]
    in_addresses.mpu_addr.channels = [["R_acc_x","R_acc_y","R_acc_z"],
                                      ["L_acc_x","L_acc_y","L_acc_z"]
                                     ]
    in_addresses.mpu_addr.vals = [0x68, 0X69]
    
    in_addresses.mpu_reg_addr = collections.namedtuple('mpu_reg_addr', 'desc vals')
    #Lines 1-2 : Self-Test
    #Line  3   : Operation Mode Conditions
    #Lines 4-5 : Configuration
    #Lines 6-12: Data registers
    in_addresses.mpu_reg_addr.desc = ["TEST_GYRO_X","TEST_GYRO_Y","TEST_GYRO_Z",
                                      "TEST_ACC_X","TEST_ACC_Y","TEST_ACC_Z",
                                      "SMPLRT_DIV","CONFIG","PWR_MGMT_1",
                                      "GYRO_CONFIG","ACC_CONFIG","ACC_CONFIG2",
                                      "WOM_THR","FIFO_EN","INT_ENABLE",
                                      "ACCEL_XOUT_H","ACCEL_XOUT_L",
                                      "ACCEL_YOUT_H","ACCEL_YOUT_L",
                                      "ACCEL_ZOUT_H","ACCEL_ZOUT_L",
                                      "TEMP_OUT_H","TEMP_OUT_L",
                                      "GYRO_XOUT_H","GYRO_XOUT_L",
                                      "GYRO_YOUT_H","GYRO_YOUT_L",
                                      "GYRO_ZOUT_H","GYRO_ZOUT_L",
                                      ]
    in_addresses.mpu_reg_addr.vals = [0x00,0x01,0x02,
                                      0x0D,0x0E,0x0F,
                                      0x19,0x1A,0x6B,
                                      0x1B,0x1C,0x1D,
                                      0x1F,0x23,0x38,                                     
                                      0x3B,0x3C,
                                      0x3D,0x3E,
                                      0x3F,0x40,
                                      0x41,0x42,
                                      0x43,0x44,
                                      0x45,0x46,
                                      0x47,0x48]
    
    in_addresses.magn_addr = collections.namedtuple('magn_addr','desc vals')
    in_addresses.magn_addr.desc = ["AK8963 (Magnetometer)"]
    in_addresses.magn_addr.vals = [0x0C]
    
    in_addresses.magn_reg_addr = collections.namedtuple('magn_reg_addr', 'desc vals')
    #Line 1 : Status/Control
    #Line 2 : Self-Test
    #Line 3 : Data
    in_addresses.magn_reg_addr.desc = ["AK8963_ST1","AK8963_ST2","AK8963_CNTL",
                                       "ASTC",
                                       "HXL","HXH","HYL","HYH","HZL","HZH"]
    in_addresses.magn_reg_addr.vals = [0x02,0x09,0x0A,
                                       0x0C,
                                       0x03,0x04,0x05,0x06,0x07,0x08]
    
    # Input module channels for Clock (not used due to address conflict)
    #in_addresses.clock_addr = collections.namedtuple('clock_addr', 'desc vals')
    #in_addresses.clock_addr.desc= ["Nothing"]
    #in_addresses.clock_addr.vals= [0x00]
    
    # Input module channels OpenBCI Board (EEG)
    # EEG channel labels not defined, since they are included in objects.openbci.info["eeg_names"]
    # 
    in_addresses.eeg = '/dev/ttyUSB0'
    in_addresses.eeg_board_id = 2
    # in_addresses.eeg_channels = ["FP1","FP2","C3","C4","T5","T6","O1","O2",
                                 # "F7","F8","FC1","FC2","T3","T4","CP1","CP2",
                                 # "Head_Accx","Head_Accy","Head_Accz"
                                # ]
    in_addresses.eeg_extra_channels = ["Accel_x","Accel_y","Accel_z"]+\
                                        ["Unknown","D11_dig","D12_dig","D13_dig","D12_anmode","D17","D18",
                                        "D11_ana","D12_ana","D13_ana"]+\
                                        ["timestamp","marker"]
    
    # Return output
    return in_addresses
    
#################################################

# Output addresses
def out_addr():
    
    out_addresses = collections.namedtuple('out_addresses', 'fes wheelchair')
    out_addresses.fes = "/dev/ttyUSB1"
    out_addresses.wheelchair= ""
    
    # Return output
    return out_addresses

#################################################

# Parameters for configuration of external devices
def exp_params():
    
    exp = collections.namedtuple('exp',['ads_rate','ads_gain',
        'fchoice','smplrt_div','dlpfcfg',
        'fes_baudrate','fes_bytesize','fes_parity','fes_stopbits',
        'fes_timeout','fes_write_timeout','fes_xonxoff',
        'fes_rtscts','fes_dsrdtr'])
    
    # ADS
    exp.ads_rate = 3300
    exp.ads_gain = 2
    
    # MPU
    #  Sampling Rate
    #   -1KHz : Fchoice=3     / DLPFCFG=1,2,3,4,5,6 / SMPLRT_DIV=0
    #   -8KHz : Fchoice=3     / DLPFCFG=0,7         / SMPLRT_DIV=0
    #   -32KHz: Fchoice=0,1,2 / DLPFCFG=-           / SMPLRT_DIV=0
    exp.fchoice = 2
    exp.smplrt_div = 0
    #exp.dlpfcfg = 0
    
    # OpenBCI
    #  -markiv_eeg_scale: Multiply uVolts_per_count to convert the channels_data to uVolts
    #  -markiv_aux_scale: Multiply accel_G_per_count to convert the aux_data to G
    exp.markiv_timeout = 4
    exp.markiv_eeg_scale = (4500000)/24/(2**23-1) #uV/count
    exp.markiv_aux_scale = 0.002 / (2**4)
    exp.markiv_num_samples = 45000
    exp.read_board_samples = 1 # how many samples to read with read_current_board_data
    exp.markiv_file = ''
    #exp.markiv_eeg_chans = 16
    #exp.markiv_aux_chans = 3
    #exp.markiv_srate = 125
    #exp.markiv_datafile = "file://%filename%:w"  
    
    # FES
    exp.fes_baudrate=115200
    exp.fes_bytesize=serial.EIGHTBITS
    exp.fes_parity="N"
    exp.fes_stopbits=serial.STOPBITS_ONE
    exp.fes_timeout=0
    exp.fes_write_timeout=None
    exp.fes_xonxoff=False
    exp.fes_rtscts=False
    exp.fes_dsrdtr=False
    
    # Clock
    
    # Return output
    return exp

#################################################

# Preprocessing parameters
def preprocess_params():
    
    preprocess_pars = collections.namedtuple('preprocess_pars',
                                             ['force_scalein','force_scaleout',
                                             'flex_scalein','flex_scaleout'])
    
    # EEG
    
    # Head IMU
    
    # EMG
    
    # ECG
    
    # Body IMU
    
    # Pressure
    #Rescale inputs to force min and max values
    #-input range: force_scalein
    #-output range: force_scaleout
    preprocess_pars.force_scalein = [1.2,2.2]
    preprocess_pars.force_scaleout = [0,3]
    
    # Flex
    #Rescale inputs to force min and max values
    #-input range: flex_scalein
    #-output range: flex_scaleout
    preprocess_pars.flex_scalein = [0.7,1.1]
    preprocess_pars.flex_scaleout = [0,2]
    
    # Wheelchair
    
    # FES
    
    # Return output
    return preprocess_pars

#################################################

# Parameters for feature extraction
def feature_params():
    
    featextract = collections.namedtuple('featextract', '')
    
    # EEG
    
    # EMG
    
    # IMU (Body)
    
    # Pressure
    
    # Flex
    
    # IMU (Wheelchair)
    
    # Return output
    return featextract

#################################################

# Parameters for feature processing and generation of outputs
def process_params():
    
    process_pars = collections.namedtuple('process_pars', ['wheelchair_states','gait_states',
                                                           'thresholds_gait','thresholds_eeg',
                                                           'thresholds_emg',
                                                           'fes_current','fes_pulse_width',
                                                           'channel_mode'])
    
    # Wheelchair out_states
    process_pars.wheelchair_states = ['Forward', 'Backward', 'Right', 'Left', 'Stop']
    
    # Gait states
    process_pars.gait_states = ['stance','midstance_l','heelstrike_r','toeoff_l',
                   'midstance_r','heelstrike_l','toeoff_r']
    
    # Gait thresholds
    force_heel_th = 1.8
    force_toe_th = 1.8
    flex_knee_th = 1
    imu_x = 1
    imu_y = 1
    imu_z = 1 # Irrelevant based on sensor placement
    process_pars.thresholds_gait = [force_heel_th, force_toe_th, flex_knee_th, imu_x, imu_y]
    
    # EEG thresholds
    eeg_alpha = 1
    eeg_beta = 1
    eeg_gamma = 1
    eeg_delta = 1
    eeg_theta = 1
    process_pars.thresholds_eeg = [eeg_delta,eeg_theta,eeg_alpha,eeg_beta,eeg_gamma]
    
    # EMG thresholds
    emg_tibialis = 1
    emg_gastrocnemius = 1
    process_pars.thresholds_emg = [emg_tibialis,emg_gastrocnemius]
    
    # FES command
    # -channel_mode: 0 - channel list mode (initialisation)
    #                1 - channel list mode (update)
    #                2 - channel list mode (stop)
    #                3 - single pulse mode
    # -current     : pulse amplitude in mA
    # -pulse_width : pulse duration in ms
    process_pars.channel_mode = 3
    process_pars.fes_current = 120
    process_pars.fes_pulse_width = 200
    
    # Wheelchair command
    
    # Return output
    return process_pars

#################################################

# Feedback parameters
def feedback_params():
    
    feedback_pars = collections.namedtuple('feedback_pars',
        ['none'])
    
    # Feedback displays
    
    # FES command vs FES output
    
    # FES output vs Movement
    
    # Wheelchair command vs Movement
    
    # Return output
    return feedback_pars   
    
#################################################

# Protocol stimuli
# task_type = 1: Walking
# task_type = 2: Wheelchair
def protocol_stimuli(task_type):
    
    protocol_pars = collections.namedtuple('protocol_pars',
        ['stimuli'])
    
    if task_type == 1:
        #protocol_pars.task = 'walking'
        protocol_pars.stimuli = [['Real right step', 'Real left step', 'Real 4 steps'],
                                 ['Imaginary right step', 'Imaginary left step', 'Imaginary 4 steps']]

    else:
        #protocol_pars.task = 'wheelchair'
        protocol_pars.stimuli = [['Stop','Forward','Backward','Right','Left']]
    
    # Return output
    return protocol_pars
