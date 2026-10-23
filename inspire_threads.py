import threading,multiprocessing
import inspire_interface, inspire_datarecord, inspire_objects, inspire_dataprocess

# Potentially required packages for multiprocessing/threading
#import ctypes
#ctypes.CDLL('libX11.so.6').XInitThreads()
#include <X11/Xlib.h>
#XInitThreads()

#################################################
# Functions for Parallel Threads/Processes

# Stream OpenBCI data (DEPRECATED)
# NOTE: Use 1st command for threading, 2nd for multiprocessing
def openbci_stream(board): 
    openbci_task=threading.Thread(target=inspire_objects.board_stream,args=[board],daemon = True)
    #openbci_task=multiprocessing.Process(target=inspire_objects.board_stream,args=[board],daemon = True)
    return openbci_task

# Manage Interface display
# NOTE: Use 1st command for threading, 2nd for multiprocessing
#def monitor_display_task():
def monitor_display_task(pygame):
    mon_task = threading.Thread(target=inspire_interface.monitor, args=[pygame],daemon = True)
    #mon_task = multiprocessing.Process(target=inspire_interface.monitor, args=[pygame],daemon = True)
    return mon_task

# Manage GPIO recording
# NOTE: Use 1st command for threading, 2nd for multiprocessing
def record_task(objects, pars, process):
#def record_task(objects, pars, process, conn):
    
    inspire_datarecord.recording = True
    #inspire_datarecord.recording = multiprocessing.Value('i')
    #inspire_datarecord.recording.value = True
        
    rec_task=threading.Thread(target=inspire_datarecord.record,args=[objects, pars, process],daemon = True)
    #rec_task=multiprocessing.Process(target=inspire_datarecord.record,args=[objects, pars, process, conn],daemon = True)
    return rec_task

# Manage feedback display
# NOTE: Use 1st command for threading, 2nd for multiprocessing
def feedback_display_task(pygame, screen, pars, canvas):
#def feedback_display_task(pars):
#def feedback_display_task(pygame, screen, pars, canvas, conn):
    fdb_display_task=threading.Thread(target=inspire_interface.feedback_display,args=[pygame, screen, pars, canvas],daemon = True)
    #fdb_display_task=multiprocessing.Process(target=inspire_interface.feedback_display,args=[pygame, screen, pars, canvas, conn],daemon = True)
    return fdb_display_task

# Manage real-time processing
# NOTE: Use 1st command for threading, 2nd for multiprocessing
def process_task(objects, pars, process, feedback, task_type, guide,filt, shared_powers):
#def process_task(objects, channels, pars, process, task_type, guide, conn):
    process_task=threading.Thread(target=inspire_dataprocess.data_process,args=[objects, pars, process, feedback, task_type, guide,filt,shared_powers],daemon = True)
    #process_task=multiprocessing.Process(target=inspire_dataprocess.data_process,args=[objects, channels, pars, process, task_type, guide, conn],daemon = True)
    return process_task
