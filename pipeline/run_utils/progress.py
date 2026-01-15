"""
Progress parsing and display utilities
"""

import sys, re


def parse_progress(log_line, state):
    """
    Parse progress from Snakemake log line.
    Extracts total jobs from job stats, counts "Finished job" messages,
    and tracks current job and subject being processed.
    
    Args:
        log_line: Single line from Snakemake log
        state: Dictionary to track parsing state across calls
        
    Returns:
        Number of jobs completed so far
    """
    # Extract total jobs from Snakemake output (appears once at start)
    # Format: "total                             1002"
    if 'total' in log_line and not state.get('total_jobs'):
        match = re.search(r'total\s+(\d+)', log_line)
        if match:
            state['total_jobs'] = int(match.group(1))
    
    # Extract current rule/job being executed
    # Format: "rule hsf_segmentation:"
    if log_line.startswith('rule '):
        match = re.match(r'rule\s+(\w+):', log_line)
        if match:
            state['current_rule'] = match.group(1)
    
    # Extract current subject from wildcards
    # Format: "    wildcards: subject=04, session=1"
    if 'wildcards:' in log_line and 'subject=' in log_line:
        match = re.search(r'subject=(\d+)', log_line)
        if match:
            state['current_subject'] = match.group(1)
    
    # Count finished jobs
    if "Finished job" in log_line:
        state['current_jobs'] = state.get('current_jobs', 0) + 1
        return state['current_jobs']
    
    return state.get('current_jobs', 0)


def print_progress_bar(current, total, prefix='', suffix='', length=40, spinner_frame=0):
    """
    Print a progress bar to stderr (so it's visible in terminal).
    
    Args:
        current: Current progress value
        total: Total value (100% completion)
        prefix: Text before the progress bar
        suffix: Text after the progress bar
        length: Character length of the bar
        spinner_frame: Frame number for spinner animation
    """
    if total == 0:
        percent = 0
    else:
        percent = min(100, int(100 * current / total))
    
    filled_length = int(length * current / total) if total > 0 else 0
    bar = '█' * filled_length + '░' * (length - filled_length)
    
    # Spinner animation
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    spin = spinner[spinner_frame % len(spinner)]
    
    # Use \r to overwrite the same line
    print(f'\r{prefix} [{current}/{total}] |{bar}| {percent}% {spin} {suffix}', 
          end='', file=sys.stderr, flush=True)
