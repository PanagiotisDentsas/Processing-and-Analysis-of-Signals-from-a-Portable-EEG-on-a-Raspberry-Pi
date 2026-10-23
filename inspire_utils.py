import time
import psutil
'''
def print_performance(start_time):
    """
    Stops the stopwatch, calculates execution delay and CPU usage, 
    and prints a clean dashboard to the terminal.
    """
    # 1. Stop the stopwatch
    end_time = time.perf_counter()
    
    # 2. Calculate the metrics
    time_delay_ms = (end_time - start_time) * 1000 
    cpu_usage = psutil.cpu_percent()
    
    # 3. Print the dashboard
    print(f"⏱️ Delay: {time_delay_ms:.2f} ms | 💻 CPU: {cpu_usage}% ")
    
    # Return the numbers just in case you want to use them later
    return time_delay_ms, cpu_usage
'''
import time
import psutil

def print_performance(start_time):
    """
    Stops the stopwatch, calculates execution delay, CPU usage, 
    and Pi temperature with absolutely minimal processing overhead.
    """
    # 1. Stop the stopwatch instantly
    end_time = time.perf_counter()
    time_delay_ms = (end_time - start_time) * 1000 
    
    # 2. CPU Usage (psutil is written in C, so it is already very fast)
    cpu_usage = psutil.cpu_percent()
    
    # 3. Ultra-Fast Temperature Read (Zero subprocess overhead)
    try:
        # Read directly from the Pi's thermal zone file
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            # The Pi stores temp in millidegrees (e.g., 48000 = 48.0 C)
            temperature = float(f.readline()) / 1000.0
            temp_display = f"{temperature:.1f}°C"
    except Exception:
        # Fallback if running on Windows/Mac
        temperature = 0.0
        temp_display = "N/A"
    
    # 4. Print the dashboard
    print(f"⏱️ Delay: {time_delay_ms:.2f} ms | 💻 CPU: {cpu_usage}% | 🌡️ Temp: {temp_display}")
    
    return time_delay_ms, cpu_usage, temperature
    
