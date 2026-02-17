#!/usr/bin/env python3
"""
CSC Puhti Pipeline Runner

Interactive wrapper for running the hippocampus radiomic feature extraction
pipeline on CSC's Puhti cluster using SLURM + Apptainer.

Features:
  - Interactive or CLI-driven project configuration
  - Dynamic Snakemake profile generation (project number, paths, tmpdir)
  - CSC-specific environment setup (shared TMPDIR, Apptainer bind mounts)
  - Real-time progress bar driven by Snakemake log output

Usage:
  # Interactive (prompts for project, paths, etc.)
  python run_csc.py

  # Non-interactive
  python run_csc.py --project 2001988 \\
      --bids-root /scratch/project_2001988/user/Dataset \\
      --sif /scratch/project_2001988/user/Containers/hippocampus-pipeline.sif

  # Dry run
  python run_csc.py --dry-run
"""

import argparse
import getpass
import os
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(SCRIPT_DIR, "config", "profiles", "csc")
PROFILE_PATH = os.path.join(PROFILE_DIR, "config.yaml")

SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

RULE_DISPLAY = {
    "hsf_segmentation": "HSF Seg",
    "split_label": "Split",
    "combine_labels": "Combine",
    "mesh_per_label": "Mesh",
    "mesh_combined": "Mesh (comb)",
    "extract_pyradiomics_per_label": "Radiomics",
    "extract_pyradiomics_combined": "Radiomics (comb)",
    "extract_curvature_per_label": "Curvature",
    "extract_curvature_combined": "Curvature (comb)",
    "aggregate_subject_features": "Aggregate",
    "aggregate_all_subjects": "Summary",
    "generate_rulegraph": "DAG",
}

MIN_SNAKEMAKE_MAJOR = 8

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(text):
    """Print a section banner to stderr."""
    w = 70
    print(f"\n{'=' * w}", file=sys.stderr)
    print(f"  {text}", file=sys.stderr)
    print(f"{'=' * w}\n", file=sys.stderr)


def info(msg):
    print(f"  {msg}", file=sys.stderr)


def ok(msg):
    print(f"  ✓ {msg}", file=sys.stderr)


def err(msg):
    print(f"  ✗ {msg}", file=sys.stderr)


def prompt(label, default=None):
    """Prompt user for input, returning *default* on empty reply."""
    if default:
        value = input(f"  {label} [{default}]: ").strip()
        return value if value else default
    while True:
        value = input(f"  {label}: ").strip()
        if value:
            return value
        print("    (required — please enter a value)")


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------

def check_snakemake():
    """Verify that Snakemake >= 8 is on PATH and return the version string."""
    try:
        r = subprocess.run(
            ["snakemake", "--version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, check=True,
        )
        ver = r.stdout.strip()
        major = int(ver.split(".")[0])
        if major < MIN_SNAKEMAKE_MAJOR:
            err(f"Snakemake {ver} found — need >= {MIN_SNAKEMAKE_MAJOR}.0.0")
            info("Try: module load snakemake/8.x  or  pip install 'snakemake>=8'")
            return None
        return ver
    except FileNotFoundError:
        err("snakemake not found in PATH")
        info("Try: module load snakemake")
        return None
    except (subprocess.CalledProcessError, ValueError):
        err("Could not determine snakemake version")
        return None


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def gather_config(args):
    """Collect all settings from CLI flags + interactive prompts."""
    username = getpass.getuser()
    interactive = not (args.project and args.bids_root and args.sif)

    if interactive:
        banner("Hippocampus Pipeline — CSC Setup")

    # --- Project number ---
    project_num = args.project
    if not project_num:
        project_num = prompt("CSC project number (e.g., 2001988)")
    project_num = project_num.replace("project_", "")
    project = f"project_{project_num}"
    base = f"/scratch/{project}/{username}"

    # --- BIDS root ---
    bids_root = args.bids_root
    if not bids_root:
        bids_root = prompt("BIDS dataset root", f"{base}/Dataset")

    # --- Derivatives ---
    deriv_default = os.path.join(bids_root, "derivatives")
    derivatives_root = args.derivatives_root or (
        prompt("Derivatives output dir", deriv_default) if interactive else deriv_default
    )

    # --- SIF path ---
    sif_default = f"{base}/Containers/hippocampus-pipeline.sif"
    sif_path = args.sif or (
        prompt("Container SIF path", sif_default) if interactive else sif_default
    )

    # --- Partition ---
    partition = args.partition or (
        prompt("SLURM partition", "small") if interactive else "small"
    )

    return {
        "project": project,
        "project_num": project_num,
        "username": username,
        "bids_root": bids_root,
        "derivatives_root": derivatives_root,
        "sif_path": sif_path,
        "partition": partition,
        "tmpdir": f"{base}/tmp",
        "scratch_project": f"/scratch/{project}",
        "jobs": args.jobs,
        "latency_wait": args.latency_wait,
        "retries": args.retries,
    }


def print_summary(cfg):
    """Print configuration summary table."""
    sep = "─" * 55
    print(f"\n  {sep}", file=sys.stderr)
    for label, value in [
        ("Project", cfg["project"]),
        ("Username", cfg["username"]),
        ("BIDS root", cfg["bids_root"]),
        ("Derivatives", cfg["derivatives_root"]),
        ("Container", cfg["sif_path"]),
        ("Partition", cfg["partition"]),
        ("Tmp dir", cfg["tmpdir"]),
        ("Max jobs", cfg["jobs"]),
    ]:
        print(f"  {label:<14} {value}", file=sys.stderr)
    print(f"  {sep}", file=sys.stderr)


def validate_paths(cfg):
    """Return a list of error strings for missing paths."""
    errors = []
    if not os.path.isdir(cfg["bids_root"]):
        errors.append(f"BIDS root not found: {cfg['bids_root']}")
    if not os.path.isfile(cfg["sif_path"]):
        errors.append(f"SIF container not found: {cfg['sif_path']}")
    return errors


# ---------------------------------------------------------------------------
# Profile generation
# ---------------------------------------------------------------------------

def write_profile(cfg):
    """Write config/profiles/csc/config.yaml with the current settings."""
    os.makedirs(PROFILE_DIR, exist_ok=True)

    p = cfg["project"]
    sp = cfg["scratch_project"]
    content = textwrap.dedent(f"""\
        # Auto-generated by run_csc.py — {datetime.now():%Y-%m-%d %H:%M:%S}
        # Project: {p}

        executor: slurm

        jobs: {cfg['jobs']}
        keep-going: true
        latency-wait: {cfg['latency_wait']}
        retries: {cfg['retries']}
        printshellcmds: true
        rerun-incomplete: true
        local-cores: 1

        default-resources:
          - slurm_account={p}
          - slurm_partition={cfg['partition']}
          - mem_mb=8000
          - runtime=120
          - "tmpdir='{cfg['tmpdir']}'"

        software-deployment-method:
          - apptainer

        apptainer-args: "--bind {sp}:{sp}:rw --env HSF_HOME=/users/$USER/.hsf"
    """)

    with open(PROFILE_PATH, "w") as f:
        f.write(content)
    return PROFILE_PATH


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

def setup_environment(cfg):
    """Prepare env vars for Apptainer + SLURM."""
    os.makedirs(cfg["tmpdir"], exist_ok=True)
    os.environ["TMPDIR"] = cfg["tmpdir"]
    for var in ("SINGULARITY_BIND", "APPTAINER_BIND"):
        os.environ.pop(var, None)


# ---------------------------------------------------------------------------
# Progress tracking
# ---------------------------------------------------------------------------

def parse_line(line, st):
    """Parse one Snakemake log line and update state *st*."""
    stripped = line.strip()

    # Authoritative progress: "M of T steps (PP%) done"
    m = re.search(r"(\d+)\s+of\s+(\d+)\s+steps.*?done", stripped)
    if m:
        st["done"] = int(m.group(1))
        st["total"] = int(m.group(2))
        return

    # Total from Job stats table: "total        503"
    if re.match(r"total\s+\d+", stripped) and not st.get("total"):
        m = re.search(r"total\s+(\d+)", stripped)
        if m:
            st["total"] = int(m.group(1))

    # Fallback per-job counter
    if "Finished job" in stripped:
        st["done"] = st.get("done", 0) + 1

    # Current rule
    m2 = re.match(r"\s*(?:local)?rule\s+(\w+):", stripped)
    if m2:
        st["rule"] = m2.group(1)

    # Current subject
    if "wildcards:" in stripped and "subject=" in stripped:
        m3 = re.search(r"subject=(\S+?)(?:,|$)", stripped)
        if m3:
            st["subject"] = m3.group(1)

    # SLURM submissions (informational)
    if "Submitted" in stripped and "external jobid" in stripped:
        st["submitted"] = st.get("submitted", 0) + 1

    # Errors
    if "Error in rule" in stripped:
        m4 = re.search(r"Error in rule (\w+)", stripped)
        if m4:
            st.setdefault("errors", []).append(m4.group(1))


def render_bar(st, prefix="Pipeline"):
    """Redraw the single-line progress bar on stderr."""
    done = st.get("done", 0)
    total = st.get("total")
    frame = st.get("_frame", 0)
    st["_frame"] = frame + 1
    spin = SPINNER[frame % len(SPINNER)]

    rule = st.get("rule", "")
    subj = st.get("subject", "")
    tag = ""
    if subj and rule:
        tag = f" | sub-{subj} {RULE_DISPLAY.get(rule, rule[:12])}"

    if total and total > 0:
        pct = min(100, int(100 * done / total))
        blen = 40
        filled = int(blen * done / total)
        bar = "█" * filled + "░" * (blen - filled)
        print(
            f"\r  {prefix} [{done}/{total}] |{bar}| {pct}% {spin}{tag}     ",
            end="", file=sys.stderr, flush=True,
        )
    elif done > 0:
        print(
            f"\r  {prefix} [{done}/?] {spin} Waiting for job stats...{tag}     ",
            end="", file=sys.stderr, flush=True,
        )
    else:
        submitted = st.get("submitted", 0)
        if submitted:
            print(
                f"\r  {prefix} {spin} Submitted {submitted} SLURM job(s)...     ",
                end="", file=sys.stderr, flush=True,
            )


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

def run_pipeline(cfg, profile_path, *, dry_run=False, force=False, clean=False):
    """Execute Snakemake with live progress tracking. Returns True on success."""

    # Optional .snakemake cleanup
    sm_dir = os.path.join(SCRIPT_DIR, ".snakemake")
    if clean and os.path.isdir(sm_dir):
        info(f"Removing {sm_dir} ...")
        shutil.rmtree(sm_dir, ignore_errors=True)
        ok("Cleaned .snakemake metadata")

    # Build command
    rel_profile = os.path.relpath(profile_path, SCRIPT_DIR)
    cmd = [
        "snakemake",
        "--snakefile", "workflow/Snakefile",
        "--profile", rel_profile,
        "--config",
        f"bids_root={cfg['bids_root']}",
        f"derivatives_root={cfg['derivatives_root']}",
        f"container_image={cfg['sif_path']}",
    ]
    if dry_run:
        cmd.append("--dry-run")
    if force:
        cmd.append("--forceall")

    # Log file
    log_base = os.path.join(cfg["derivatives_root"], "logs")
    os.makedirs(log_base, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_base, f"run_csc_{ts}.log")

    mode_label = "DRY RUN" if dry_run else "EXECUTION"
    banner(f"Pipeline {mode_label}")
    info(f"Log:     {log_file}")
    info(f"Command: snakemake --profile {rel_profile} --config ...")
    print(file=sys.stderr)

    # --- Dry run: show output interactively ---
    if dry_run:
        result = subprocess.run(cmd, cwd=SCRIPT_DIR, check=False)
        return result.returncode == 0

    # --- Real run with progress tracking ---
    state = {"done": 0, "total": None, "_frame": 0}
    stop = threading.Event()

    def tailer():
        """Tail the log file and update progress state."""
        while not stop.is_set() and not os.path.exists(log_file):
            time.sleep(0.2)
        if stop.is_set():
            return
        try:
            with open(log_file, "r") as fh:
                while not stop.is_set():
                    line = fh.readline()
                    if line:
                        parse_line(line, state)
                        render_bar(state)
                    else:
                        time.sleep(0.3)
        except Exception:
            pass

    tail_thread = threading.Thread(target=tailer, daemon=True)
    tail_thread.start()

    start_time = time.time()
    try:
        with open(log_file, "w") as lf:
            result = subprocess.run(
                cmd,
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=SCRIPT_DIR,
                check=False,
            )
    except KeyboardInterrupt:
        print(f"\n\n  Interrupted by user.", file=sys.stderr)
        info(f"SLURM jobs may still be running — check: squeue -A {cfg['project']}")
        info(f"Cancel them with: scancel -A {cfg['project']}")
        sys.exit(130)
    finally:
        stop.set()
        tail_thread.join(timeout=2)

    # Duration
    elapsed = time.time() - start_time
    hours, rem = divmod(int(elapsed), 3600)
    mins, secs = divmod(rem, 60)
    duration = f"{hours}h {mins}m {secs}s" if hours else f"{mins}m {secs}s"

    # Final pass to capture any lines the tail thread missed
    try:
        with open(log_file, "r") as fh:
            for line in fh:
                parse_line(line, state)
    except Exception:
        pass

    done = state.get("done", 0)
    total = state.get("total", done)
    errors = state.get("errors", [])

    # Newline after progress bar
    print(file=sys.stderr)

    # --- Summary ---
    banner("Summary")
    info(f"Duration:  {duration}")
    info(f"Jobs:      {done}/{total}")

    if result.returncode == 0 and not errors:
        ok("Pipeline completed successfully")
        info(f"Output:    {cfg['derivatives_root']}/summary/all_features.csv")
        return True
    else:
        err(f"Pipeline failed (exit code {result.returncode})")
        if errors:
            unique = list(dict.fromkeys(errors))  # dedupe, preserve order
            info(f"Failed in: {', '.join(unique[:10])}")
        info(f"Log:       {log_file}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run hippocampus pipeline on CSC Puhti (SLURM + Apptainer)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              # Interactive setup
              python run_csc.py

              # Full CLI (no prompts)
              python run_csc.py --project 2001988 \\
                  --bids-root /scratch/project_2001988/user/Dataset \\
                  --sif /scratch/project_2001988/user/Containers/pipeline.sif

              # Dry run to see planned jobs
              python run_csc.py --project 2001988 -n

              # Clean stale metadata and force re-run
              python run_csc.py --clean --force
        """),
    )

    # Required-ish (prompted interactively if absent)
    parser.add_argument("--project", help="CSC project number (e.g., 2001988)")
    parser.add_argument("--bids-root", help="BIDS dataset root directory")
    parser.add_argument("--derivatives-root", help="Derivatives output (default: <bids>/derivatives)")
    parser.add_argument("--sif", help="Path to Apptainer .sif container")

    # SLURM tuning
    parser.add_argument("--partition", default=None, help="SLURM partition (default: small)")
    parser.add_argument("--jobs", type=int, default=100, help="Max concurrent SLURM jobs (default: 100)")
    parser.add_argument("--latency-wait", type=int, default=120, help="Seconds to wait for output files (default: 120)")
    parser.add_argument("--retries", type=int, default=1, help="Retries per failed job (default: 1)")

    # Execution control
    parser.add_argument("-n", "--dry-run", action="store_true", help="Show planned jobs without executing")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--force", action="store_true", help="Force re-run all rules (--forceall)")
    parser.add_argument("--clean", action="store_true", help="Remove .snakemake/ metadata before running")

    args = parser.parse_args()

    # 1. Prerequisites
    info("Checking prerequisites...")
    ver = check_snakemake()
    if not ver:
        sys.exit(1)
    ok(f"Snakemake {ver}")
    print(file=sys.stderr)

    # 2. Configuration
    cfg = gather_config(args)
    print_summary(cfg)

    # 3. Validate paths (skip for dry-run since paths may not exist locally)
    if not args.dry_run:
        errs = validate_paths(cfg)
        if errs:
            for e in errs:
                err(e)
            sys.exit(1)

    # 4. Confirm
    if not args.yes and not args.dry_run:
        answer = input("\n  Proceed? [Y/n]: ").strip().lower()
        if answer and answer != "y":
            print("  Aborted.", file=sys.stderr)
            sys.exit(0)

    # 5. Environment setup
    print(file=sys.stderr)
    info("Setting up environment...")
    setup_environment(cfg)
    ok(f"TMPDIR = {cfg['tmpdir']}")
    ok("Cleared stale SINGULARITY_BIND / APPTAINER_BIND")

    profile = write_profile(cfg)
    ok(f"Profile written to {os.path.relpath(profile, SCRIPT_DIR)}")

    # 6. Run
    success = run_pipeline(
        cfg, profile,
        dry_run=args.dry_run,
        force=args.force,
        clean=args.clean,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
