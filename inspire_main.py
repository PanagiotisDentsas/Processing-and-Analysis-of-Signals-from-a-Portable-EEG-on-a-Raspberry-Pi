# Import path
import sys,multiprocessing
import csv
sys.path.insert(1, '/home/pi/Desktop/Documents/INSPiRE/Package')

#################################################

# Import modules (Python & custom modules)
import time
from datetime import datetime
import inspire_config, inspire_objects, inspire_threads, inspire_datarecord, inspire_interface,inspire_filters
import inspire_filters

# Commands for reloading modules in case of an update during debugging
#from importlib import reload
#reload(inspire_objects) # declare which module you wish to reload

#################################################

# Set session variables
participant = "panagiotis"      # Participant name / identifier
exp_time    = datetime.now() # Save current timestamp for session folder
scale       = True           # Rescale input values or store raw data
guide       = False          # Provide stimulus for movement
task_type   = 2              # 1: walking, 2: wheelchair
process     = True           # Produce real-time output
feedback    = True           # Produce real-time feedback
save_data   = True           # Save session data
filt        = True           # Apply frequency filters in the data
#################################################

# Initialise parameters
pars = inspire_config.params(participant,exp_time,save_data,scale,guide,process,task_type) # Experiment parameters
# print(pars._fields)

#################################################

# Create objects & Define data headers
objects, msg = inspire_objects.objects(pars)
pars.session.gpio_headers, pars.session.openbci_headers = inspire_objects.data_headers(objects,pars)

#################################################
# Create Shared variables
# NOTE: Needed if multiprocessing library (vs threading) is used
#pygame = multiprocessing.Array('i',[0])
#screen = multiprocessing.Array('i',[0])
#canvas = multiprocessing.Array('i',[0])

#################################################

# Initialise interface
# (NOTE: use 1st instead of 2nd command if threading is used instead of multiprocessing)
[pygame,screen,pos,canvas] = inspire_interface.interface(objects,pars.config,msg)
#[pygame.value,screen.value,pos,canvas.value] = inspire_interface.interface(objects,pars.config,msg)

###########asking if filteres shoulld be applied

filt = False  # Default to False
#the filtering choice is made with confirm
shared_powers = {"theta": 0.0, "beta": 0.0}



#######
# Ask for confirmation
# (NOTE: use 1st instead of 2nd command if threading is used instead of multiprocessing)
[cont,pos,filt] = inspire_interface.confirm(pygame,screen,pars.config,pos,filt)

#[cont,pos] = inspire_interface.confirm(pygame.value,screen.value,pars.config,pos)



if not cont:
    exit()

#################################################
# Create Pipe for data exchange among parallel processes
# NOTE: Only if multiprocessing is used
#  -parent_conn: data sender
#  -child_conn : data receiver
#conn1,conn2 = multiprocessing.Pipe(duplex=True)

#################################################
# Create Threads

# Thread for monitoring display
thread1 = inspire_threads.monitor_display_task(pygame)
#thread1 = inspire_threads.monitor_display_task()

# Recording thread
# NOTE: use 1st instead of 2nd command if threading is used
thread2 = inspire_threads.record_task(objects, pars, process)
#thread2 = inspire_threads.record_task(objects, pars, process, conn1)

# Live feedback thread
# NOTE: use 1st instead of 2nd command if threading is used
thread3 = inspire_threads.feedback_display_task(pygame, screen, pars, canvas)
#thread3 = inspire_threads.feedback_display_task(pygame, screen, pars, canvas, conn2)

# Real-time data processing
# NOTE: use 1st instead of 2nd command if threading is used
thread4 = inspire_threads.process_task(objects, pars, process, feedback, task_type, guide,filt,shared_powers)
#thread4 = inspire_threads.process_task(objects, channels, pars, process, task_type, guide, conn2)

# Start OpenBCI Stream (DEPRECATED)
# if objects.openbci[0].obj == []:
#     print("OpenBCI stream not started")
#     thread0 = 0
# else:
#     thread0 = inspire_threads.openbci_stream(objects.openbci[0].obj)
#     thread0.start()
#     time.sleep(2) # Wait until stream starts and vars are created

#################################################
# Test variables for multiprocessing (1st 2 commands for array, 2nd 2 commands for value)
#inspire_datarecord.gpiodata = multiprocessing.Array('i',[1,1])
#inspire_datarecord.gpiodata.value=[]
#inspire_datarecord.test = multiprocessing.Value('i')
#inspire_datarecord.test.value = 1

#################################################
# Start Threads
thread1.start() # monitor_display_task
thread2.start() # record_task
if feedback:
    thread3.start() # feedback_display_task
if process:
    thread4.start() # process_task

# Command for testing, 1st for threading, 2nd for multiprocessing
#print(inspire_datarecord.recording)
#print(inspire_datarecord.recording.value)

#################################################
# Monitor state of threads
import pygame
while True:
    time.sleep(0.05)
    try:
        pygame.event.pump()
        pygame.display.update()
    except pygame.error:
        pass
    threads = [thread1.is_alive(),
               thread2.is_alive(),
               thread3.is_alive(),
               thread4.is_alive()
               ]
    #print(threads)
    if not any(threads):
        if any(pars.session.openbci_headers):
            objects.openbci.stop_stream()
            objects.openbci.release_session()
            objects.openbci.release_all_sessions()
        
        # DEPRECATED
#         if not isinstance(thread0, int):
#             objects.openbci.obj.stop_stream()
#             print("OpenBCI stream ended")
#             #thread0.join()
        break

thread1.join() # monitor_display_task
thread2.join() # record_task
if feedback:
    thread3.join() # feedback_display_task
if process:
    thread4.join() # process_task
print("Finished")

#################################################
# Get recorded data from connection
# NOTE: Only needed if multiprocessing is used
#gpiodata = conn2.recv()

#################################################
# Save session data
# NOTE: use 1st instead of 2nd command if threading is used
inspire_datarecord.save_sessiondata(pars,objects,inspire_datarecord.gpiodata)
#inspire_datarecord.save_sessiondata(pars,objects,gpiodata)








if filt == True:
 
        
    
    #the filtering happens inside the saving function
    inspire_datarecord.save_filteredeegdata(pars,objects,inspire_datarecord.gpiodata)
    import inspire_filters
    #inspire_filters.visualize_filter_results(pars.config.openbcidatafile, pars.config.fopenbcidatafile)
    

#################################################
## Close
input("Press Enter to close...") 
#thread1.join() # monitor_display_task
#thread2.join() # record_task
