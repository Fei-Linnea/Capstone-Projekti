"""
Snakemake profile and arguments builder for dynamic configuration.

Allows runtime configuration of Snakemake parameters via environment variables,
enabling container images to remain immutable while still being configurable.
"""

import os


def get_snakemake_args(profile_path: str, batch_size: int = None) -> list:
    """
    Build Snakemake command-line arguments with dynamic resource configuration.
    
    Reads resource settings from environment variables and overrides the config file values.
    This allows the container image to remain static while being configurable at runtime.
    
    Args:
        profile_path: Path to Snakemake profile (e.g., 'config/profiles/tyks')
        batch_size: Optional batch size for pipeline processing
        
    Returns:
        List of Snakemake arguments to pass to subprocess
        
    Environment Variables (optional):
        SNAKEMAKE_JOBS: Number of parallel jobs (default: 8)
        SNAKEMAKE_CORES: Total CPU cores to use (default: 16)
        SNAKEMAKE_MEM_MB: Memory per job in MB (default: 4000)
        SNAKEMAKE_THREADS: Threads per job (default: 2)
        
    Example:
        >>> args = get_snakemake_args('config/profiles/tyks')
        >>> # Returns: ['--profile', 'config/profiles/tyks', '--jobs', '8', '--cores', '16', ...]
    """
    
    # Read from environment variables with sensible defaults
    jobs = int(os.environ.get("SNAKEMAKE_JOBS", "8"))
    cores = int(os.environ.get("SNAKEMAKE_CORES", "16"))
    mem_mb = int(os.environ.get("SNAKEMAKE_MEM_MB", "4000"))
    threads = int(os.environ.get("SNAKEMAKE_THREADS", "2"))
    
    # Build the argument list
    args = [
        "--profile", profile_path,
        "--jobs", str(jobs),
        "--cores", str(cores),
        "--set-resources", f"mem_mb={mem_mb}",
        "--set-resources", f"threads={threads}",
    ]
    
    return args


def print_snakemake_config(profile_path: str) -> None:
    """
    Print the effective Snakemake configuration (for debugging/logging).
    
    Shows which values come from environment variables vs defaults.
    
    Args:
        profile_path: Path to Snakemake profile
    """
    jobs = int(os.environ.get("SNAKEMAKE_JOBS", "8"))
    cores = int(os.environ.get("SNAKEMAKE_CORES", "16"))
    mem_mb = int(os.environ.get("SNAKEMAKE_MEM_MB", "4000"))
    threads = int(os.environ.get("SNAKEMAKE_THREADS", "2"))
    
    env_jobs = "SNAKEMAKE_JOBS" in os.environ
    env_cores = "SNAKEMAKE_CORES" in os.environ
    env_mem = "SNAKEMAKE_MEM_MB" in os.environ
    env_threads = "SNAKEMAKE_THREADS" in os.environ
    
    print(f"\n{'='*60}")
    print(f"Snakemake Configuration")
    print(f"{'='*60}")
    print(f"Profile:        {profile_path}")
    print(f"Jobs:           {jobs}{' (default)' if not env_jobs else ''}")
    print(f"Cores:          {cores}{' (default)' if not env_cores else ''}")
    print(f"Memory/Job:     {mem_mb} MB{' (default)' if not env_mem else ''}")
    print(f"Threads/Job:    {threads}{' (default)' if not env_threads else ''}")
    print(f"{'='*60}\n")
