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
Examples:
    # Full command example, run with defaults from profile
    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks

    # Run with custom batch size
    Flag: --batch-size 20

    # Override cores at runtime
    Flags: --cores 32

    # Override rule threads for specific rule
    Flag: --set-threads hsf_segmentation=4

    # Dry run (show what would be done)
    Flag: --dry-run

    # Process specific subjects
    Flag: --subjects 01 02 03 04 05

    # Use a custom BIDS pattern
    Flag: --bids-pattern "sub-*/ses-1/anat/*_T1w.nii.gz"

    # Complete example with multiple overrides
    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks --batch-size 10 --cores 16 --set-threads hsf_segmentation=4
        """
    )
    
    # Configuration arguments
    parser.add_argument(
        "--profile",
        required=True,
        help="Snakemake profile directory (e.g., config/profiles/tyks). A config.yaml path inside the profile is also accepted."
    )
    
    # Processing arguments
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of subjects per batch (default: {DEFAULT_BATCH_SIZE})"
    )

    # Snakemake overrides (optional)
    parser.add_argument(
        "--cores",
        nargs="?",
        const="all",
        default=None,
        help=(
            "Override Snakemake cores (default from the selected Snakemake profile). "
            "Provide a number (e.g., --cores 16) or pass --cores without a value to use all available cores."
        )
    )
    parser.add_argument(
        "--set-threads",
        action="append",
        default=None,
        help="Override rule threads (e.g., hsf_segmentation=4). Can be used multiple times."
    )
    
    parser.add_argument(
        "--bids-pattern",
        default=DEFAULT_BIDS_PATTERN,
        help=f"BIDS glob pattern under /data (default: {DEFAULT_BIDS_PATTERN})"
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
        help="Specific subjects to process (default: auto-discover from /data)"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove intermediate files after successful completion, keeping only summary/all_features.csv"
    )
    
    args = parser.parse_args()

    # Fixed container paths (end users shouldn't need to set these)
    pipeline_dir = DEFAULT_PIPELINE_DIR
    log_base_dir = DEFAULT_LOG_BASE_DIR
    data_dir = DEFAULT_DATA_DIR
    
    # Create timestamped log directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.join(log_base_dir, timestamp)
    os.makedirs(log_dir, exist_ok=True)
    
    # Print startup banner
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"Hippocampus Radiomic Feature Extraction Pipeline", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
    print(f"Log directory: {log_dir}", file=sys.stderr)
    print(f"Profile: {args.profile}", file=sys.stderr)
    print(f"Batch size: {args.batch_size}", file=sys.stderr)
    # Load profile to display effective defaults
    # Support both directory paths (e.g. config/profiles/tyks) and
    # direct file paths (e.g. config/profiles/tyks/config.yaml).
    raw_profile_arg = args.profile
    profile_path = raw_profile_arg
    # If profile is relative, resolve against pipeline_dir (inside container
    # this is typically /app/pipeline, matching the Snakemake cwd).
    if not os.path.isabs(profile_path):
        profile_path = os.path.join(pipeline_dir, profile_path)

    # Determine the profile config file path (for reading defaults)
    if os.path.isdir(profile_path):
        profile_config_path = os.path.join(profile_path, "config.yaml")
    else:
        profile_config_path = profile_path

    # Determine the Snakemake --profile argument.
    # Snakemake expects a *directory* for --profile; if the user provided
    # a config.yaml path, convert it to the containing directory.
    if os.path.isdir(profile_path):
        snakemake_profile_arg = profile_path
    else:
        snakemake_profile_arg = os.path.dirname(profile_path)

    # Use absolute paths for robustness.
    profile_config_path = os.path.abspath(profile_config_path)
    snakemake_profile_arg = os.path.abspath(snakemake_profile_arg)

    profile_data = {}
    try:
        with open(profile_config_path, "r") as f:
            profile_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"ERROR: Profile not found: {profile_config_path}", file=sys.stderr)
        sys.exit(1)

    selected_cores = args.cores if args.cores is not None else profile_data.get("cores")
    print(f"Cores: {selected_cores}", file=sys.stderr)
    if args.set_threads:
        overrides_display = ", ".join(args.set_threads)
        print(f"Thread overrides: {overrides_display}", file=sys.stderr)
    else:
        print("Thread overrides: none (using defaults)", file=sys.stderr)

    if args.dry_run:
        print("Mode: DRY RUN", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)

    # Get subjects list
    if args.subjects:
        subjects = args.subjects
        print(f"Using specified subjects: {', '.join(subjects)}", file=sys.stderr)
    else:
        # Auto-discover subjects from BIDS data directory
        subjects = discover_subjects(data_dir, args.bids_pattern)
        
        if not subjects:
            print(f"ERROR: No subjects found in {data_dir}", file=sys.stderr)
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
            profile=snakemake_profile_arg,
            log_dir=log_dir,
            batch_size=args.batch_size,
            pipeline_dir=pipeline_dir,
            cores=selected_cores,
            set_threads=args.set_threads,
            subjects=subjects,
            bids_pattern=args.bids_pattern,
            dry_run=args.dry_run
        )
        
        if not success:
            failed_batches.append(batch_num)
    
    # Run aggregation if all batches succeeded
    if not failed_batches and not args.dry_run:
        aggregation_success = run_aggregation(
            profile=snakemake_profile_arg,
            log_dir=log_dir,
            pipeline_dir=pipeline_dir,
            cores=selected_cores,
            set_threads=args.set_threads,
            subjects=subjects,
            bids_pattern=args.bids_pattern,
            dry_run=args.dry_run
        )
        
        if not aggregation_success:
            failed_batches.append("aggregation")
    
    # Cleanup intermediate files if requested and pipeline succeeded
    if args.cleanup and not failed_batches:
        # Need to get derivatives_root from config/config.yaml
        config_path = os.path.join(os.path.dirname(__file__), DEFAULT_CONFIG_PATH)
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        derivatives_root = config['derivatives_root']
        
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
