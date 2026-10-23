# Import modules
import pygame,os,pylab,time
import matplotlib
matplotlib.use("Agg")
import matplotlib.backends.backend_agg as agg
import inspire_datarecord

#################################################

# Interface Initialisation
def interface(objects, pars, msg):
    global fig
    global fig_X
    global bars
    global ax
    #global canvas
    
    # Initialize pygame display
    os.environ['SDL_VIDEO_CENTERED'] = '1' #bring pygame window to center of screen
    pygame.init() #begin pygame
    pygame.display.set_caption(pars.gui_title) #set title for pygame window
    screen = pygame.display.set_mode((pars.gui_width,pars.gui_height)) #create pygame window
    
    # Display messages and update display position for next object
    pos = pars.gui_startpos
    font = pygame.font.Font(pars.gui_font, pars.gui_fontsize)
    for i in range(len(msg)):
        text = font.render(msg[i],True,pars.gui_fontcolor,pars.gui_fontbgr)
        screen.blit(text, pos)
        pygame.display.update()
        pos = [pos[0],pos[1]+20]        
    '''old display 
    # Create figure for live feedback
    fig = pylab.figure(figsize=pars.fig_size,dpi=pars.fig_dpi)
    ax = fig.subplots(1)
    ax.set_ylim([pars.ylim_min,pars.ylim_max])
    
    labels = []
    for i in range(len(objects.ads)):
        labels = labels + objects.ads[i].chan_labels
    for i in range(len(objects.mpu)):
        labels = labels + objects.mpu[i].chan_labels
#     for i in range(len(objects.openbci)):
#         labels = labels + objects.openbci[i].chan_labels
    #fig_X = channels.ads["labels"]+channels.mpu["labels"]
    fig_X = labels
    
    # bars updated by inspire_datarecord.record 
    bars = ax.bar(fig_X,[0]*len(fig_X))
    
    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    '''
    #####make a figure with the eeg features
    # Create figure for live feedback
    fig = pylab.figure(figsize=pars.fig_size,dpi=pars.fig_dpi)
    ax = fig.subplots(1)
    
    
    
    
    
    # ---> START OF THE REPLACEMENT <---
    ax.set_ylim([0, 100])
    fig_X = ['Theta ', 'Beta ']
    
    global bars, theta_text, beta_text
    
    # Start  at a small number (like 10.0) so we don't divide by zero later
    theta_peak = 10.0 
    beta_peak = 10.0
    peak_ceiling = 100.0
    bars = ax.bar(fig_X, [0, 0], color=['#f1c40f', '#2ecc71'])
    
    # Create the text objects (Positioned at X=0 and X=1)
    # ha='center' keeps them perfectly horizontally aligned inside the poles
    theta_text = ax.text(0, 0, '0.0', ha='center', va='center', color='black', fontsize=16, fontweight='bold', zorder=10)
    beta_text = ax.text(1, 0, '0.0', ha='center', va='center', color='black', fontsize=16, fontweight='bold', zorder=10)
    # ---> END OF THE REPLACEMENT <---
    
 
    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    
    
    
    return pygame,screen,pos,canvas

#################################################



'''
def ask_filter_preference(pygame,screen,pars,pos):
    font = pygame.font.Font(pars.gui_font, pars.gui_fontsize)
    msg = "Do you want to apply filters? Press Y for Yes, N for No"
    text = font.render(msg,True,pars.gui_fontcolor,pars.gui_fontbgr)
    screen.blit(text, pos)
    pos = [pos[0],pos[1]+20]
    pygame.display.update()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
               return False,pos
                    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    return True,pos
                if event.key == pygame.K_n:
                    return False,pos
'''

#########
# User confirmation request (via pygame GUI) for proceeding with the main recording
def confirm(pygame,screen,pars,pos,filt):
    
    
    font = pygame.font.Font(pars.gui_font, pars.gui_fontsize)
    
    msg = "Press  F if you want  to aplly filters or N if not"
    text = font.render(msg,True,pars.gui_fontcolor,pars.gui_fontbgr)
    screen.blit(text, pos)
    pos = [pos[0],pos[1]+20]
    pygame.display.update()
    
    loop1=True
    while loop1:
        
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                filt=False
                loop1=False
                    
            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_f:
                    filt=True
                    loop1=False
                    msg = "Filters will be applied"
                    text = font.render(msg,True,pars.gui_fontcolor,pars.gui_fontbgr)
                    screen.blit(text, pos)
                    pos = [pos[0],pos[1]+20]
                    pygame.display.update()
                if event.key == pygame.K_n:
                    filt=False
                    loop1=False
                    
                    msg = "Filters wont be applied"
                    text = font.render(msg,True,pars.gui_fontcolor,pars.gui_fontbgr)
                    screen.blit(text, pos)
                    pos = [pos[0],pos[1]+20]
                    pygame.display.update()
                    
    
    
    msg = "Press Enter to begin, Esc to abort"
    text = font.render(msg,True,pars.gui_fontcolor,pars.gui_fontbgr)
    screen.blit(text, pos)
    pos = [pos[0],pos[1]+20]
    pygame.display.update()
    
    while True:
        
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
               return False,pos,filt
                    
            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_ESCAPE:
                    return False,pos,filt
                    
                if event.key == pygame.K_RETURN:
                    return True,pos,filt

#################################################

# Monitor GUI state
# Close GUI when a specific key press is detected
# Note: Use 1st command for recording variable for threading, 2nd for multiprocessing
#def monitor():
def monitor(pygame):
    print("Display started")
    display = True
    while display:
        time.sleep(2)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                display = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    display = False
                    break
    
    inspire_datarecord.recording = False
    #inspire_datarecord.recording.value = False
    
    pygame.display.quit()
    pygame.quit()
    return

#################################################

# Refresh live feedback display
# NOTE: Use 1st command for recording variable for threading, 2nd for multiprocessing
def feedback_display(pygame,screen,pars,canvas):
#def feedback_display(pygame,screen,pars,canvas,conn):
    
    # Refresh figures
    while True:
        canvas.draw()
        canvas.flush_events()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_argb()
        size = canvas.get_width_height()
        surf = pygame.image.fromstring(raw_data, size, "ARGB")
        
        # Get data for feedback
        # NOTE: Only if multiprocessing is used instead of threading
        #m = conn.recv()
        #for i in range(len(bars)):
        #    bars[i].set_height(m[i+2])
        
        # Refresh feedback figure
        # NOTE: Check if display is open first to prevent error when the gui is closed
        #       Alternatively, use a "try-except" block
        if pygame.display.get_init():
            screen.blit(surf, (pars.config.gui_width-pars.config.fig_size[1]*pars.config.fig_dpi,0))

            #pygame.display.update() # use this command for threading, the below for multiprocessing#pygame.display.flip() # use this command for threading, the below for multiprocessing
            
	    
            #pygame.value.flip()
        else:
            return

#################################################
