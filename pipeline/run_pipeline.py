#!/usr/bin/env python3
"""
Hippocampus Radiomic Feature Extraction Pipeline Runner
Processes subjects in batches with progress tracking
"""

import argparse, os, sys, glob
from datetime import datetime
from run_utils import run_snakemake_batch, run_aggregation


def run_pipeline():
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
    run_pipeline()
