"""
Configuration defaults and constants for the pipeline runner.
Can be overridden via CLI args where applicable.
"""
import os

# ============================================================================
# Configuration defaults
# ============================================================================
DEFAULT_CONFIG_PATH = "config/config.yaml"
DEFAULT_JOBS = 8
DEFAULT_CORES = os.cpu_count() or 4
DEFAULT_BATCH_SIZE = int(os.environ.get("PIPELINE_BATCH_SIZE", "5"))
DEFAULT_PIPELINE_DIR = "/app/pipeline"
DEFAULT_LOG_BASE_DIR = "/app/logs"
DEFAULT_DATA_DIR = "/data"
DEFAULT_BIDS_PATTERN = "sub-*/ses-*/anat/*_T1w.nii.gz"

# Rule name abbreviations for progress display
RULE_DISPLAY_NAMES = {
    'hsf_segmentation': 'hsf',
    'split_label': 'split',
    'mesh_per_label': 'mesh',
    'mesh_combined': 'mesh_cmb',
    'extract_curvature_per_label': 'curv',
    'extract_curvature_combined': 'curv_cmb',
    'extract_pyradiomics_per_label': 'radiomics',
    'extract_pyradiomics_combined': 'radiomics_cmb',
    'combine_labels': 'combine',
    'aggregate_subject_features': 'aggregate'
}

# Spinner animation frames
SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
