"""
Pipeline execution API routes.

POST /api/pipeline/start   – start a new pipeline run
POST /api/pipeline/stop    – cancel a running pipeline
GET  /api/pipeline/status  – get current run state snapshot
"""

import os
import sys
import json
import subprocess
import threading
import yaml
from datetime import datetime
from flask import Blueprint, jsonify, request

from pipeline.run_utils.config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_BIDS_PATTERN,
    DEFAULT_CONFIG_PATH,
    DEFAULT_DATA_DIR,
    DEFAULT_LOG_BASE_DIR,
    DEFAULT_PIPELINE_DIR,
    RULE_DISPLAY_NAMES,
)
from pipeline.run_utils.subjects import discover_subjects
from pipeline.run_utils.progress import parse_progress
from pipeline.run_utils.logger import tail_log_file

from pipeline.web.state import run_state

pipeline_bp = Blueprint("pipeline", __name__, url_prefix="/api/pipeline")


# ── status route ─────────────────────────────────────────────────────

@pipeline_bp.route("/status", methods=["GET"])
def get_status():
    """Return current pipeline run state."""
    return jsonify(run_state.snapshot())


# ── start route ──────────────────────────────────────────────────────

@pipeline_bp.route("/start", methods=["POST"])
def start_pipeline():
    """
    Start a new pipeline run.

    Expects JSON body:
    {
        "profile": "tyks",         // required – profile name (not path)
        "batch_size": 5,           // optional
        "cores": 16,               // optional – int or "all"
        "set_threads": ["hsf_segmentation=4"], // optional
        "subjects": ["01","02"],   // optional – auto-discover if omitted
        "bids_pattern": "...",     // optional
        "dry_run": false,          // optional
        "cleanup": false           // optional
    }
    """
    if run_state.is_running:
        return jsonify({"error": "Pipeline is already running"}), 409

    data = request.get_json(force=True)
    profile_name = data.get("profile")
    if not profile_name:
        return jsonify({"error": "\"profile\" is required"}), 400

    # Build config dict from request
    config = {
        "profile": profile_name,
        "batch_size": data.get("batch_size", DEFAULT_BATCH_SIZE),
        "cores": data.get("cores"),
        "set_threads": data.get("set_threads"),
        "subjects": data.get("subjects"),
        "bids_pattern": data.get("bids_pattern", DEFAULT_BIDS_PATTERN),
        "dry_run": data.get("dry_run", False),
        "cleanup": data.get("cleanup", False),
    }

    # Resolve paths
    pipeline_dir = os.environ.get("PIPELINE_DIR", DEFAULT_PIPELINE_DIR)
    log_base_dir = os.environ.get("LOG_BASE_DIR", DEFAULT_LOG_BASE_DIR)
    data_dir = os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)

    # Create log dir
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.join(log_base_dir, timestamp)
    os.makedirs(log_dir, exist_ok=True)

    # Reset state
    run_state.reset(config, log_dir)

    # Start background runner thread
    runner = threading.Thread(
        target=_run_pipeline_thread,
        args=(config, pipeline_dir, data_dir, log_dir),
        daemon=True,
    )
    run_state._runner_thread = runner
    runner.start()

    return jsonify({"message": "Pipeline started", "log_dir": log_dir}), 202


# ── stop route ───────────────────────────────────────────────────────

@pipeline_bp.route("/stop", methods=["POST"])
def stop_pipeline():
    """Request cancellation of the running pipeline."""
    if not run_state.is_running:
        return jsonify({"error": "No pipeline is currently running"}), 400

    run_state.request_cancel()
    run_state.kill_process()
    return jsonify({"message": "Cancel requested"})


# ── background runner ────────────────────────────────────────────────

def _resolve_profile(profile_name: str, pipeline_dir: str):
    """
    Resolve a profile name to absolute paths for the config file
    and the Snakemake --profile directory argument.
    """
    profiles_base = os.path.join(pipeline_dir, "config", "profiles")
    profile_path = os.path.join(profiles_base, profile_name)

    if os.path.isdir(profile_path):
        config_path = os.path.join(profile_path, "config.yaml")
        snakemake_arg = profile_path
    else:
        config_path = profile_path
        snakemake_arg = os.path.dirname(profile_path)

    return os.path.abspath(config_path), os.path.abspath(snakemake_arg)


def _run_snakemake(cmd, log_file, pipeline_dir, batch_num=None, total_batches=None):
    """
    Run a snakemake subprocess, tailing the log for progress updates.
    Returns True on success.
    """
    progress_state = {
        "current_jobs": 0,
        "total_jobs": None,
        "shown_initial": False,
        "spinner_frame": 0,
    }
    stop_event = threading.Event()

    def _progress_cb(line):
        parse_progress(line, progress_state)
        run_state.update_progress(
            current_jobs=progress_state.get("current_jobs", 0),
            total_jobs=progress_state.get("total_jobs"),
            current_rule=progress_state.get("current_rule", ""),
            current_subject=progress_state.get("current_subject", ""),
        )

    tail_thread = threading.Thread(
        target=tail_log_file,
        args=(log_file, stop_event, _progress_cb),
        daemon=True,
    )
    tail_thread.start()

    try:
        with open(log_file, "w") as f:
            proc = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=pipeline_dir,
            )
            run_state.set_process(proc)
            proc.wait()

        stop_event.set()
        tail_thread.join(timeout=2.0)

        return proc.returncode == 0

    except Exception as e:
        stop_event.set()
        run_state.set_status("failed", str(e))
        return False


def _run_pipeline_thread(config: dict, pipeline_dir: str, data_dir: str, log_dir: str):
    """Background thread that mirrors run_pipeline.py main() flow."""
    try:
        profile_name = config["profile"]
        batch_size = config["batch_size"]
        cores = config.get("cores")
        set_threads = config.get("set_threads")
        bids_pattern = config.get("bids_pattern", DEFAULT_BIDS_PATTERN)
        dry_run = config.get("dry_run", False)
        cleanup = config.get("cleanup", False)

        # 1. Resolve profile
        profile_config_path, snakemake_profile_arg = _resolve_profile(profile_name, pipeline_dir)
        if not os.path.isfile(profile_config_path):
            run_state.set_status("failed", f"Profile not found: {profile_config_path}")
            return

        with open(profile_config_path, "r") as f:
            profile_data = yaml.safe_load(f) or {}

        selected_cores = cores if cores is not None else profile_data.get("cores")

        # 2. Discover subjects
        run_state.update_progress(phase="discovering")
        if config.get("subjects"):
            subjects = config["subjects"]
        else:
            subjects = discover_subjects(data_dir, bids_pattern)

        if not subjects:
            run_state.set_status("failed", f"No subjects found in {data_dir}")
            return

        run_state.update_progress(subjects_total=len(subjects))

        # 3. Split into batches
        batches = []
        for i in range(0, len(subjects), batch_size):
            batches.append(subjects[i : i + batch_size])

        total_batches = len(batches)
        run_state.update_progress(
            phase="batching",
            total_batches=total_batches,
        )

        # 4. Process batches
        failed_batches = []
        for batch_num, batch_subjects in enumerate(batches, start=1):
            if run_state.cancel_requested:
                run_state.set_status("failed", "Cancelled by user")
                return

            run_state.update_progress(
                batch_num=batch_num,
                current_jobs=0,
                total_jobs=None,
                current_rule="",
                current_subject="",
            )

            log_file = os.path.join(log_dir, f"snakemake_batch_{batch_num:03d}.log")

            cmd = [
                "snakemake",
                "--snakefile", "workflow/Snakefile",
                "--profile", snakemake_profile_arg,
                "--config",
                f"bids_root={data_dir}",
                f"derivatives_root={os.path.join(data_dir, 'derivatives')}",
                f"batch_size={batch_size}",
                f"batch_number={batch_num - 1}",
                f"log_dir={log_dir}",
            ]

            if subjects:
                cmd.append(f"subjects={json.dumps([str(s) for s in subjects])}")
            if bids_pattern:
                cmd.append(f"bids_pattern={bids_pattern}")
            if selected_cores is not None:
                cmd.extend(["--cores", str(selected_cores)])
            if set_threads:
                for entry in set_threads:
                    cmd.extend(["--set-threads", entry])
            if dry_run:
                cmd.append("--dry-run")

            if dry_run:
                # Write the command to the log file for reference
                with open(log_file, "w") as f:
                    f.write(f"DRY RUN: {' '.join(cmd)}\n")
                run_state.update_progress(
                    completed_batches=run_state.progress["completed_batches"] + [batch_num],
                )
                continue

            success = _run_snakemake(cmd, log_file, pipeline_dir, batch_num, total_batches)

            if success:
                run_state.update_progress(
                    completed_batches=run_state.progress["completed_batches"] + [batch_num],
                )
            else:
                failed_batches.append(batch_num)
                run_state.update_progress(
                    failed_batches=run_state.progress["failed_batches"] + [batch_num],
                )

        # 5. Aggregation
        if not failed_batches and not dry_run:
            run_state.update_progress(phase="aggregating", current_jobs=0, total_jobs=None)

            agg_log = os.path.join(log_dir, "snakemake_aggregation.log")
            cmd = [
                "snakemake",
                "--snakefile", "workflow/Snakefile",
                "--profile", snakemake_profile_arg,
                "--config",
                f"bids_root={data_dir}",
                f"derivatives_root={os.path.join(data_dir, 'derivatives')}",
                f"batch_size=0",
                f"log_dir={log_dir}",
            ]
            if subjects:
                cmd.append(f"subjects={json.dumps([str(s) for s in subjects])}")
            if bids_pattern:
                cmd.append(f"bids_pattern={bids_pattern}")
            if selected_cores is not None:
                cmd.extend(["--cores", str(selected_cores)])
            if set_threads:
                for entry in set_threads:
                    cmd.extend(["--set-threads", entry])

            agg_ok = _run_snakemake(cmd, agg_log, pipeline_dir)
            if not agg_ok:
                failed_batches.append("aggregation")
                run_state.update_progress(
                    failed_batches=run_state.progress["failed_batches"] + ["aggregation"],
                )

        # 6. Cleanup
        if cleanup and not failed_batches:
            run_state.update_progress(phase="cleaning")
            try:
                cfg_path = os.path.join(pipeline_dir, DEFAULT_CONFIG_PATH)
                with open(cfg_path, "r") as f:
                    pipeline_cfg = yaml.safe_load(f) or {}
                derivatives_root = pipeline_cfg.get("derivatives_root", "/data/derivatives")

                from pipeline.run_utils.cleanup import cleanup_with_confirmation
                cleanup_with_confirmation(derivatives_root=derivatives_root, dry_run=dry_run)
            except Exception as e:
                # Cleanup errors are non-fatal
                pass

        # 7. Final status
        run_state.update_progress(phase="done")
        if failed_batches:
            run_state.set_status("failed", f"Failed batches: {failed_batches}")
        else:
            run_state.set_status("completed")

    except Exception as e:
        run_state.set_status("failed", str(e))
