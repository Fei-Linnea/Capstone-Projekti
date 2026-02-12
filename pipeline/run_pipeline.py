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
  # Run with defaults from profile
  python run_pipeline.py

  # Run with custom batch size
  python run_pipeline.py --batch-size 20

  # Override jobs and cores at runtime
  python run_pipeline.py --jobs 16 --cores 32

  # Override rule threads for specific rule
  python run_pipeline.py --set-threads hsf_segmentation=4

  # Dry run (show what would be done)
  python run_pipeline.py --dry-run

  # Process specific subjects
  python run_pipeline.py --subjects 01 02 03 04 05

  # Complete example with multiple overrides
  python run_pipeline.py --batch-size 10 --jobs 8 --cores 16 --dry-run
        """
    )
    
    # Configuration arguments
    parser.add_argument(
        "--profile",
        required=True,
        help="Snakemake profile config (e.g., config/profiles/tyks/config.yaml)"
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
        "--jobs",
        type=int,
        default=None,
        help="Override Snakemake jobs (default from config/config.yaml)"
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=None,
        help="Override Snakemake cores (default from config/config.yaml)"
    )
    parser.add_argument(
        "--set-threads",
        action="append",
        default=None,
        help="Override rule threads (e.g., hsf_segmentation=4). Can be used multiple times."
    )
    parser.add_argument(
        "--set-resources",
        action="append",
        default=None,
        help="Override rule resources (e.g., hsf_segmentation:mem_mb=16000). Can be used multiple times."
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
    print(f"Profile: {args.profile}", file=sys.stderr)
    print(f"Pipeline dir: {args.pipeline_dir}", file=sys.stderr)
    print(f"Data dir: {args.data_dir}", file=sys.stderr)
    print(f"Batch size: {args.batch_size}", file=sys.stderr)
    # Load profile to display effective defaults
    # Support both directory paths (e.g. config/profiles/tyks) and
    # direct file paths (e.g. config/profiles/tyks/config.yaml).
    profile_path = args.profile
    # If profile is relative, resolve against pipeline_dir (inside container
    # this is typically /app/pipeline, matching the Snakemake cwd).
    if not os.path.isabs(profile_path):
        profile_path = os.path.join(args.pipeline_dir, profile_path)

    # If a directory is given, assume standard Snakemake profile layout
    # with a config.yaml file inside it.
    if os.path.isdir(profile_path):
        profile_config_path = os.path.join(profile_path, "config.yaml")
    else:
        profile_config_path = profile_path

    profile_data = {}
    try:
        with open(profile_config_path, "r") as f:
            profile_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"ERROR: Profile not found: {profile_config_path}", file=sys.stderr)
        sys.exit(1)

    effective_jobs = args.jobs if args.jobs is not None else profile_data.get("jobs")
    effective_cores = args.cores if args.cores is not None else profile_data.get("cores")
    mem_mb = None
    default_resources = profile_data.get("default-resources")
    # Snakemake profiles typically use a list like ["mem_mb=4000"]
    # but allow dict-style as well; handle both.
    if isinstance(default_resources, dict):
        mem_mb = default_resources.get("mem_mb")
    elif isinstance(default_resources, list):
        for item in default_resources:
            if isinstance(item, str) and item.startswith("mem_mb="):
                value = item.split("=", 1)[1]
                try:
                    mem_mb = int(value)
                except ValueError:
                    mem_mb = value
                break

    print(f"Jobs: {effective_jobs}", file=sys.stderr)
    print(f"Cores: {effective_cores}", file=sys.stderr)
    print(f"Memory/job: {mem_mb if mem_mb is not None else 'n/a'}", file=sys.stderr)
    if args.set_threads:
        overrides_display = ", ".join(args.set_threads)
        print(f"Thread overrides: {overrides_display}", file=sys.stderr)
    else:
        print("Thread overrides: none (profile defaults)", file=sys.stderr)

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
            profile=args.profile,
            log_dir=log_dir,
            batch_size=args.batch_size,
            pipeline_dir=args.pipeline_dir,
            jobs=args.jobs,
            cores=args.cores,
            set_threads=args.set_threads,
            set_resources=args.set_resources,
            dry_run=args.dry_run
        )
        
        if not success:
            failed_batches.append(batch_num)
    
    # Run aggregation if all batches succeeded
    if not failed_batches and not args.dry_run:
        aggregation_success = run_aggregation(
            profile=args.profile,
            log_dir=log_dir,
            pipeline_dir=args.pipeline_dir,
            jobs=args.jobs,
            cores=args.cores,
            set_threads=args.set_threads,
            set_resources=args.set_resources,
            dry_run=args.dry_run
        )
        
        if not aggregation_success:
            failed_batches.append("aggregation")
    
    # Cleanup intermediate files if requested and pipeline succeeded
    if args.cleanup and not failed_batches:
        # Read derivatives_root from pipeline config file
        pipeline_config_path = os.path.join(args.pipeline_dir, "config", "config.yaml")
        derivatives_root = "/data/derivatives"
        try:
            with open(pipeline_config_path, "r") as f:
                cfg = yaml.safe_load(f) or {}
                derivatives_root = cfg.get("derivatives_root", derivatives_root)
        except Exception:
            # Fall back to default if config cannot be read
            pass

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
