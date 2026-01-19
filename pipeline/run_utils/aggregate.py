"""
Snakemake aggregation step after batch processing
"""

import sys
import os
import subprocess


def run_aggregation(config_file, profile_dir, cores, log_dir, pipeline_dir,
                    dry_run=False):
    """
    Run the aggregation step after all batches are complete.
    This combines features from all subjects into final output files.
    
    Args:
        config_file: Path to config.yaml
        profile_dir: Snakemake profile directory
        cores: Number of CPU cores to use
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
