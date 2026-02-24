"""
Configuration & discovery API routes.

GET /api/config/profiles          – list available Snakemake profiles
GET /api/config/profiles/<name>   – profile YAML contents
GET /api/config/defaults          – pipeline default constants
GET /api/subjects                 – discover subjects from /data
"""

import os
import yaml
from flask import Blueprint, jsonify, request

from pipeline.run_utils.config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_BIDS_PATTERN,
    DEFAULT_DATA_DIR,
    DEFAULT_LOG_BASE_DIR,
    DEFAULT_PIPELINE_DIR,
    DEFAULT_CONFIG_PATH,
    RULE_DISPLAY_NAMES,
)
from pipeline.run_utils.subjects import discover_subjects

config_bp = Blueprint("config", __name__, url_prefix="/api/config")
subjects_bp = Blueprint("subjects", __name__, url_prefix="/api")


# ── helpers ──────────────────────────────────────────────────────────

def _profiles_dir() -> str:
    """Resolve the absolute path to the profiles directory."""
    # In-container: /app/pipeline/config/profiles
    # Dev: <repo>/pipeline/config/profiles
    base = os.environ.get("PIPELINE_DIR", DEFAULT_PIPELINE_DIR)
    return os.path.join(base, "config", "profiles")


def _pipeline_config_path() -> str:
    base = os.environ.get("PIPELINE_DIR", DEFAULT_PIPELINE_DIR)
    return os.path.join(base, DEFAULT_CONFIG_PATH)


# ── profile routes ───────────────────────────────────────────────────

@config_bp.route("/profiles", methods=["GET"])
def list_profiles():
    """Return list of available profile names (directory names under profiles/)."""
    profiles_path = _profiles_dir()
    if not os.path.isdir(profiles_path):
        return jsonify({"profiles": [], "error": f"Profiles dir not found: {profiles_path}"}), 200

    profiles = []
    for entry in sorted(os.listdir(profiles_path)):
        entry_path = os.path.join(profiles_path, entry)
        if os.path.isdir(entry_path) and os.path.isfile(os.path.join(entry_path, "config.yaml")):
            profiles.append(entry)

    return jsonify({"profiles": profiles})


@config_bp.route("/profiles/<name>", methods=["GET"])
def get_profile(name: str):
    """Return the parsed YAML contents of a named profile."""
    profile_yaml = os.path.join(_profiles_dir(), name, "config.yaml")
    if not os.path.isfile(profile_yaml):
        return jsonify({"error": f"Profile not found: {name}"}), 404

    with open(profile_yaml, "r") as f:
        data = yaml.safe_load(f) or {}

    return jsonify({"name": name, "config": data})


# ── defaults route ───────────────────────────────────────────────────

@config_bp.route("/defaults", methods=["GET"])
def get_defaults():
    """Return pipeline default constants."""
    # Also read pipeline config.yaml for hsf_params etc.
    pipeline_cfg = {}
    cfg_path = _pipeline_config_path()
    if os.path.isfile(cfg_path):
        with open(cfg_path, "r") as f:
            pipeline_cfg = yaml.safe_load(f) or {}

    return jsonify({
        "batch_size": DEFAULT_BATCH_SIZE,
        "bids_pattern": DEFAULT_BIDS_PATTERN,
        "data_dir": DEFAULT_DATA_DIR,
        "log_base_dir": DEFAULT_LOG_BASE_DIR,
        "pipeline_dir": DEFAULT_PIPELINE_DIR,
        "rule_display_names": RULE_DISPLAY_NAMES,
        "pipeline_config": pipeline_cfg,
    })


# ── subject discovery ────────────────────────────────────────────────

@subjects_bp.route("/subjects", methods=["GET"])
def list_subjects():
    """Discover subjects from the BIDS data directory."""
    data_dir = os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)
    bids_pattern = request.args.get("bids_pattern", DEFAULT_BIDS_PATTERN)
    subjects = discover_subjects(data_dir, bids_pattern)
    return jsonify({"subjects": subjects, "count": len(subjects), "bids_pattern": bids_pattern})
