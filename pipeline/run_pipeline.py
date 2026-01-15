#!/usr/bin/env python3
"""
Hippocampus Radiomic Feature Extraction Pipeline Runner
Processes subjects in batches with progress tracking
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import threading
import time
import re


def tail_log_file(log_file, stop_event, progress_callback):
    """
    Tail a log file and call progress_callback for each new line.
    Runs in a separate thread.
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


def parse_progress(log_line, state):
    """
    Parse progress from Snakemake log line.
    Extracts total jobs from job stats, counts "Finished job" messages,
    and tracks current job and subject being processed.
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
    if total is None or total == 0:
        percent = 0
        filled_length = 0
    else:
        percent = min(100, int(100 * current / total))
        filled_length = int(length * current / total)
    
    bar = '█' * filled_length + '░' * (length - filled_length)
    
    # Spinner animation
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    spin = spinner[spinner_frame % len(spinner)]
    
    # Use \r to overwrite the same line
    print(f'\r{prefix} [{current}/{total if total else "?"}] |{bar}| {percent}% {spin} {suffix}', 
          end='', file=sys.stderr, flush=True)


def run_snakemake_batch(batch_subjects, batch_num, total_batches, config_file, 
                        profile_dir, cores, log_dir, batch_size, dry_run=False):
    """
    Run Snakemake for a batch of subjects with progress tracking.
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
        "--configfile", config_file,
        "--config", 
        f"batch_size={batch_size}",
        f"batch_number={batch_num - 1}",
        f"log_dir={log_dir}",
        "--cores", str(cores),
        "--rerun-incomplete",
        "--keep-going"
    ]
    
    if profile_dir:
        cmd.extend(["--profile", profile_dir])
    
    if dry_run:
        cmd.append("--dry-run")
        print(f"DRY RUN: {' '.join(cmd)}", file=sys.stderr)
        return True
    
    # Debug: show the actual command being executed
    print(f"[CMD] {' '.join(cmd)}", file=sys.stderr)
    print(f"", file=sys.stderr)
    
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
        
        # Shorten rule names for display
        rule_display = {
            'hsf_segmentation': 'hsf',
            'split_label': 'split',
            'mesh_per_label': 'mesh',
            'mesh_combined': 'mesh_cmb',
            'extract_curvature_per_label': 'curv',
            'extract_curvature_combined': 'curv_cmb',
            'extract_pyradiomics_per_label': 'radiomics',
            'extract_pyradiomics_combined': 'radiomics_cmb',
            'combine_labels': 'combine',
            'aggregate_subject_features': 'aggregate'
        }
        
        status_suffix = ''
        if current_subject and current_rule:
            rule_short = rule_display.get(current_rule, current_rule[:10])
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
            spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            spin = spinner[spinner_frame % len(spinner)]
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
                cwd="/app/pipeline",
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


def run_aggregation(config_file, profile_dir, cores, log_dir, dry_run=False):
    """
    Run the aggregation step after all batches are complete.
    This combines features from all subjects into final output files.
    """
    log_file = os.path.join(log_dir, "snakemake_aggregation.log")
    
    print(f"\n{'='*80}", file=sys.stderr)
    print("Running final aggregation...", file=sys.stderr)
    print(f"Log: {log_file}", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)
    
    # Run aggregation for all subjects (batch_size=0 means process all)
    cmd = [
        "snakemake",
        "--snakefile", "workflow/Snakefile",
        "--configfile", config_file,
        "--config",
        f"batch_size=0",
        f"log_dir={log_dir}",
        "--cores", str(cores),
        "--rerun-incomplete",
        "aggregate_all_subjects"
    ]
    
    if profile_dir:
        cmd.extend(["--profile", profile_dir])
    
    if dry_run:
        cmd.append("--dry-run")
        print(f"DRY RUN: {' '.join(cmd)}", file=sys.stderr)
        return True
    
    try:
        with open(log_file, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd="/app/pipeline",
                check=False
            )
        
        if result.returncode != 0:
            print(f"\n⚠️  Aggregation failed with exit code {result.returncode}", 
                  file=sys.stderr)
            print(f"Check log file: {log_file}", file=sys.stderr)
            return False
        
        print("✓ Aggregation complete\n", file=sys.stderr)
        return True
        
    except Exception as e:
        print(f"\n❌ Error during aggregation: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run hippocampus feature extraction pipeline in batches"
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to config file (default: config/config.yaml)"
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Snakemake profile directory"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of subjects per batch (default: 5)"
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=4,
        help="Number of CPU cores to use (default: 4)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without executing jobs"
    )
    parser.add_argument(
        "--subjects",
        nargs="+",
        help="Specific subjects to process (default: all from config)"
    )
    
    args = parser.parse_args()
    
    # Create timestamped log directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = f"/app/logs/{timestamp}"
    os.makedirs(log_dir, exist_ok=True)
    
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"Hippocampus Radiomic Feature Extraction Pipeline", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
    print(f"Log directory: {log_dir}", file=sys.stderr)
    print(f"Config: {args.config}", file=sys.stderr)
    print(f"Batch size: {args.batch_size}", file=sys.stderr)
    print(f"Cores: {args.cores}", file=sys.stderr)
    if args.dry_run:
        print("Mode: DRY RUN", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)
    
    # Get subjects list
    if args.subjects:
        subjects = args.subjects
    else:
        # Auto-discover subjects from BIDS data directory
        import glob
        bids_root = "/data"
        pattern = os.path.join(bids_root, "sub-*/ses-*/anat/*_T1w.nii.gz")
        files = glob.glob(pattern)
        
        subject_set = set()
        for f in files:
            basename = os.path.basename(f)
            import re
            match = re.match(r'sub-([^_]+)_ses-([^_]+)_T1w\.nii\.gz', basename)
            if match:
                subject_set.add(match.group(1))
        
        subjects = sorted(list(subject_set))
        
        if not subjects:
            print("ERROR: No subjects found in /data", file=sys.stderr)
            sys.exit(1)
    
    # Split into batches
    batches = []
    for i in range(0, len(subjects), args.batch_size):
        batches.append(subjects[i:i + args.batch_size])
    
    total_batches = len(batches)
    batch_word = "batch" if total_batches == 1 else "batches"
    print(f"Processing {len(subjects)} subjects in {total_batches} {batch_word}\n", 
          file=sys.stderr)
    
    # Process batches
    failed_batches = []
    for batch_num, batch_subjects in enumerate(batches, start=1):
        success = run_snakemake_batch(
            batch_subjects,
            batch_num,
            total_batches,
            args.config,
            args.profile,
            args.cores,
            log_dir,
            args.batch_size,
            args.dry_run
        )
        
        if not success:
            failed_batches.append(batch_num)
    
    # Run aggregation if all batches succeeded
    if not failed_batches and not args.dry_run:
        aggregation_success = run_aggregation(
            args.config,
            args.profile,
            args.cores,
            log_dir,
            args.dry_run
        )
        
        if not aggregation_success:
            failed_batches.append("aggregation")
    
    # Final summary
    print(f"\n{'='*80}", file=sys.stderr)
    print("Pipeline Summary", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"Total subjects: {len(subjects)}", file=sys.stderr)
    print(f"Total batches: {total_batches}", file=sys.stderr)
    
    if failed_batches:
        print(f"❌ Failed batches: {', '.join(map(str, failed_batches))}", file=sys.stderr)
        print(f"Exit code: 1", file=sys.stderr)
        sys.exit(1)
    else:
        print("✓ All batches completed successfully", file=sys.stderr)
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
        print(f"Exit code: 0", file=sys.stderr)
    
    print(f"{'='*80}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
