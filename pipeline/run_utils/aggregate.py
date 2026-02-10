"""
Snakemake aggregation step after batch processing
"""

import sys
import os
import subprocess


def run_aggregation(profile, log_dir, pipeline_dir,
                    jobs=None, cores=None,
                    set_threads=None, set_resources=None,
                    dry_run=False):
    """
    Run the aggregation step after all batches are complete.
    This combines features from all subjects into final output files.
    
    Args:
        profile: Path to Snakemake profile config
        log_dir: Directory for logs
        pipeline_dir: Working directory for Snakemake
        dry_run: If True, don't execute, just show commands
        
    Returns:
        True if successful, False otherwise
    """
    log_file = os.path.join(log_dir, "snakemake_aggregation.log")
    
    print(f"\n{'='*80}", file=sys.stderr)
    print("Running final aggregation...", file=sys.stderr)
    print(f"Log: {log_file}", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)
    
    # Run aggregation for all subjects (batch_size=0 means process all)
    if not profile:
        print("ERROR: --profile is required", file=sys.stderr)
        return False

    cmd = [
        "snakemake",
        "--snakefile", "workflow/Snakefile",
        "--profile", profile,
        "--config",
        f"batch_size=0",
        f"log_dir={log_dir}"
    ]

    # Add Snakemake execution flags (profile provides other defaults)
    if jobs is not None:
        cmd.extend(["--jobs", str(jobs)])
    if cores is not None:
        cmd.extend(["--cores", str(cores)])
    # if set_threads:
    #     for entry in set_threads:
    #         cmd.extend(["--set-threads", entry])
    # if set_resources:
    #     for entry in set_resources:
    #         cmd.extend(["--set-resources", entry])
    if dry_run:
        cmd.append("--dry-run")

    # Add target rule at the end (after all flags)
    cmd.append("aggregate_all_subjects")
    
    if dry_run:
        print(f"DRY RUN: {' '.join(cmd)}", file=sys.stderr)
        return True
    
    try:
        with open(log_file, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=pipeline_dir,
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
