"""
Snakemake batch execution
"""

import os
import sys
import subprocess
import threading

from .config import RULE_DISPLAY_NAMES, SPINNER_FRAMES
from .logger import tail_log_file
from .progress import parse_progress, print_progress_bar

def run_snakemake_batch(batch_subjects, batch_num, total_batches, profile,
                        log_dir, batch_size, pipeline_dir,
                        jobs=None, cores=None,
                        set_threads=None, set_resources=None,
                        dry_run=False):
    """
    Run Snakemake for a batch of subjects with progress tracking.
    
    Args:
        batch_subjects: List of subject IDs for this batch
        batch_num: Batch number (1-indexed)
        total_batches: Total number of batches
        profile: Path to Snakemake profile config
        log_dir: Directory for logs
        batch_size: Size of batch (for config)
        pipeline_dir: Working directory for Snakemake
        dry_run: If True, don't execute, just show commands
        
    Returns:
        True if successful, False otherwise
    """
    # Create subject list string
    subject_list = ",".join(batch_subjects)
    
    # Set up log file for this batch
    log_file = os.path.join(log_dir, f"snakemake_batch_{batch_num:03d}.log")
    
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"Batch {batch_num}/{total_batches}: Processing {len(batch_subjects)} subjects", 
          file=sys.stderr)
    print(f"Subjects: {subject_list}", file=sys.stderr)
    print(f"Log: {log_file}", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)
    
    # Build Snakemake command with batch parameters
    # Note: batch_number is 0-indexed for Snakefile
    # All config values must be in a single --config argument
    cmd = [
        "snakemake",
        "--snakefile", "workflow/Snakefile",
        "--profile", profile,
        "--config",
        f"batch_size={batch_size}",
        f"batch_number={batch_num - 1}",
        f"log_dir={log_dir}"
    ]

    # Add Snakemake execution flags (profile provides other defaults)
    if jobs is not None:
        cmd.extend(["--jobs", str(jobs)])
    if cores is not None:
        cmd.extend(["--cores", str(cores)])
    if set_threads:
        for entry in set_threads:
            cmd.extend(["--set-threads", entry])
    if set_resources:
        for entry in set_resources:
            cmd.extend(["--set-resources", entry])
    if dry_run:
        cmd.append("--dry-run")
    
    if dry_run:
        print(f"DRY RUN: {' '.join(cmd)}", file=sys.stderr)
        return True
    
    # Progress tracking state
    progress_state = {'current_jobs': 0, 'total_jobs': None, 'shown_initial': False, 'spinner_frame': 0}
    stop_event = threading.Event()
    
    def progress_callback(line):
        """Called for each new log line"""
        jobs_done = parse_progress(line, progress_state)
        total_jobs = progress_state.get('total_jobs')
        
        # Increment spinner frame on every callback
        progress_state['spinner_frame'] = progress_state.get('spinner_frame', 0) + 1
        spinner_frame = progress_state['spinner_frame']
        
        # Build status suffix showing current job
        current_rule = progress_state.get('current_rule', '')
        current_subject = progress_state.get('current_subject', '')
        
        status_suffix = ''
        if current_subject and current_rule:
            rule_short = RULE_DISPLAY_NAMES.get(current_rule, current_rule[:10])
            status_suffix = f' | sub-{current_subject} - {rule_short}'
        
        # Show initial progress bar as soon as we have the total
        if total_jobs and not progress_state.get('shown_initial'):
            progress_state['shown_initial'] = True
            print_progress_bar(
                0,
                total_jobs,
                prefix=f'Batch {batch_num}/{total_batches}',
                suffix=status_suffix,
                spinner_frame=spinner_frame
            )
        
        if jobs_done > 0 and total_jobs:
            # Use actual total from Snakemake
            print_progress_bar(
                jobs_done,
                total_jobs,
                prefix=f'Batch {batch_num}/{total_batches}',
                suffix=status_suffix,
                spinner_frame=spinner_frame
            )
        elif jobs_done > 0:
            # Fallback: show progress without percentage until total is known
            spin = SPINNER_FRAMES[spinner_frame % len(SPINNER_FRAMES)]
            print(f'\rBatch {batch_num}/{total_batches} [{jobs_done}/?] {spin} Processing...{status_suffix}', 
                  end='', file=sys.stderr, flush=True)
    
    # Start log tailing thread
    tail_thread = threading.Thread(
        target=tail_log_file,
        args=(log_file, stop_event, progress_callback),
        daemon=True
    )
    tail_thread.start()
    
    # Run Snakemake with output redirected to log file
    try:
        with open(log_file, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=pipeline_dir,
                check=False
            )
        
        # Stop the tail thread
        stop_event.set()
        tail_thread.join(timeout=1.0)
        
        # Final progress update
        final_jobs = progress_state.get('current_jobs', 0)
        total_jobs = progress_state.get('total_jobs', final_jobs)
        print_progress_bar(
            final_jobs,
            total_jobs,
            prefix=f'Batch {batch_num}/{total_batches}',
            suffix='✓ Complete\n',
            spinner_frame=0
        )
        
        if result.returncode != 0:
            print(f"\n⚠️  Batch {batch_num} failed with exit code {result.returncode}", 
                  file=sys.stderr)
            print(f"Check log file: {log_file}", file=sys.stderr)
            return False
        
        return True
        
    except Exception as e:
        stop_event.set()
        print(f"\n❌ Error running batch {batch_num}: {e}", file=sys.stderr)
        return False
