#!/usr/bin/env python3
"""
Hippocampus Radiomic Feature Extraction Pipeline Runner
Processes subjects in batches with progress tracking

This is the main entry point for the pipeline. All utility functions
are imported from the run_utils package.
"""

import argparse, os, sys, yaml
from datetime import datetime

# Import all utilities from run_utils package
from run_utils import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_BATCH_SIZE,
    DEFAULT_PIPELINE_DIR,
    DEFAULT_LOG_BASE_DIR,
    DEFAULT_DATA_DIR,
    DEFAULT_BIDS_PATTERN,
    run_snakemake_batch,
    run_aggregation,
    discover_subjects,
    cleanup_with_confirmation
)


def main():
    """Main entry point for the pipeline runner."""
    parser = argparse.ArgumentParser(
        description="Run hippocampus feature extraction pipeline in batches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables (used as defaults if not specified via CLI):
  PIPELINE_CONFIG       Config file path (default: config/config.yaml)
  PIPELINE_BATCH_SIZE   Subjects per batch (default: 5)
  PIPELINE_DIR          Pipeline working directory (default: /app/pipeline)
  PIPELINE_LOG_DIR      Log base directory (default: /app/logs)
  PIPELINE_DATA_DIR     BIDS data directory (default: /data)
  PIPELINE_BIDS_PATTERN BIDS file pattern (default: sub-*/ses-*/anat/*_T1w.nii.gz)

Examples:
  # Run with default settings
  python run_pipeline.py

  # Run with custom batch size
  python run_pipeline.py --batch-size 20

  # Run with TYKS profile (recommended)
  python run_pipeline.py --profile config/profiles/tyks --batch-size 20

  # Dry run (show what would be done)
  python run_pipeline.py --dry-run

  # Process specific subjects
  python run_pipeline.py --subjects 01 02 03 04 05
        """
    )
    
    # Configuration arguments
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config file (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Snakemake profile directory (e.g., config/profiles/tyks)"
    )
    
    # Processing arguments
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of subjects per batch (default: {DEFAULT_BATCH_SIZE})"
    )
    
    # Path arguments
    parser.add_argument(
        "--pipeline-dir",
        default=DEFAULT_PIPELINE_DIR,
        help=f"Pipeline working directory (default: {DEFAULT_PIPELINE_DIR})"
    )
    parser.add_argument(
        "--log-dir",
        default=DEFAULT_LOG_BASE_DIR,
        help=f"Base directory for logs (default: {DEFAULT_LOG_BASE_DIR})"
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help=f"BIDS data directory (default: {DEFAULT_DATA_DIR})"
    )
    parser.add_argument(
        "--bids-pattern",
        default=DEFAULT_BIDS_PATTERN,
        help=f"BIDS glob pattern for T1w files (default: {DEFAULT_BIDS_PATTERN})"
    )
    
    # Execution control
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without executing jobs"
    )
    parser.add_argument(
        "--subjects",
        nargs="+",
        help="Specific subjects to process (default: auto-discover from data-dir)"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove intermediate files after successful completion, keeping only summary/all_features.csv"
    )
    
    args = parser.parse_args()
    
    # Create timestamped log directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.join(args.log_dir, timestamp)
    os.makedirs(log_dir, exist_ok=True)
    
    # Print startup banner
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"Hippocampus Radiomic Feature Extraction Pipeline", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
    print(f"Log directory: {log_dir}", file=sys.stderr)
    print(f"Config: {args.config}", file=sys.stderr)
    print(f"Pipeline dir: {args.pipeline_dir}", file=sys.stderr)
    print(f"Data dir: {args.data_dir}", file=sys.stderr)
    print(f"Batch size: {args.batch_size}", file=sys.stderr)
    if args.profile:
        print(f"Profile: {args.profile}", file=sys.stderr)
    if args.dry_run:
        print("Mode: DRY RUN", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)
    
    # Get subjects list
    if args.subjects:
        subjects = args.subjects
        print(f"Using specified subjects: {', '.join(subjects)}", file=sys.stderr)
    else:
        # Auto-discover subjects from BIDS data directory
        subjects = discover_subjects(args.data_dir, args.bids_pattern)
        
        if not subjects:
            print(f"ERROR: No subjects found in {args.data_dir}", file=sys.stderr)
            print(f"Pattern used: {args.bids_pattern}", file=sys.stderr)
            sys.exit(1)
        
        print(f"Auto-discovered {len(subjects)} subjects", file=sys.stderr)
    
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
            batch_subjects=batch_subjects,
            batch_num=batch_num,
            total_batches=total_batches,
            config_file=args.config,
            profile_dir=args.profile,
            log_dir=log_dir,
            batch_size=args.batch_size,
            pipeline_dir=args.pipeline_dir,
            dry_run=args.dry_run
        )
        
        if not success:
            failed_batches.append(batch_num)
    
    # Run aggregation if all batches succeeded
    if not failed_batches and not args.dry_run:
        aggregation_success = run_aggregation(
            config_file=args.config,
            profile_dir=args.profile,
            log_dir=log_dir,
            pipeline_dir=args.pipeline_dir,
            dry_run=args.dry_run
        )
        
        if not aggregation_success:
            failed_batches.append("aggregation")
    
    # Cleanup intermediate files if requested and pipeline succeeded
    if args.cleanup and not failed_batches:
        # Need to get derivatives_root from config
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        derivatives_root = config.get('derivatives_root', '/data/derivatives')
        
        cleanup_success = cleanup_with_confirmation(
            derivatives_root=derivatives_root,
            dry_run=args.dry_run
        )
        
        if not cleanup_success:
            print("⚠ Warning: Cleanup encountered errors (pipeline results preserved)", file=sys.stderr)
    
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
