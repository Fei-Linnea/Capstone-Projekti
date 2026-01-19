"""
Log file tailing and threading utilities
"""

import os, sys, time


def tail_log_file(log_file, stop_event, progress_callback):
    """
    Tail a log file and call progress_callback for each new line.
    Runs in a separate thread.
    
    Args:
        log_file: Path to log file to tail
        stop_event: threading.Event to signal when to stop
        progress_callback: Function to call for each new line
    """
    # Wait for log file to exist
    while not stop_event.is_set():
        if os.path.exists(log_file):
            break
        time.sleep(0.1)
    
    if stop_event.is_set():
        return
    
    try:
        with open(log_file, 'r') as f:
            # Start from beginning to catch all messages
            f.seek(0, 0)
            
            while not stop_event.is_set():
                line = f.readline()
                if line:
                    progress_callback(line.strip())
                else:
                    time.sleep(0.1)  # Short sleep if no new data
    except Exception as e:
        print(f"Error tailing log: {e}", file=sys.stderr)
