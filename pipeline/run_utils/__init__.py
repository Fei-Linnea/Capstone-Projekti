"""
Utility modules for the Hippocampus Radiomic Feature Extraction Pipeline
"""

from .config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_BATCH_SIZE,
    DEFAULT_PIPELINE_DIR,
    DEFAULT_LOG_BASE_DIR,
    DEFAULT_DATA_DIR,
    DEFAULT_BIDS_PATTERN,
    RULE_DISPLAY_NAMES,
    SPINNER_FRAMES
)
from .logger import tail_log_file
from .progress import parse_progress, print_progress_bar
from .batchExecutor import run_snakemake_batch
from .aggregate import run_aggregation
from .subjects import discover_subjects
from .cleanup import cleanup_intermediate_files, cleanup_with_confirmation

__all__ = [
    # Config defaults
    'DEFAULT_CONFIG_PATH',
    'DEFAULT_BATCH_SIZE',
    'DEFAULT_PIPELINE_DIR',
    'DEFAULT_LOG_BASE_DIR',
    'DEFAULT_DATA_DIR',
    'DEFAULT_BIDS_PATTERN',
    'RULE_DISPLAY_NAMES',
    'SPINNER_FRAMES',
    # Functions
    'tail_log_file',
    'parse_progress',
    'print_progress_bar',
    'run_snakemake_batch',
    'run_aggregation',
    'discover_subjects',
    'cleanup_intermediate_files',
    'cleanup_with_confirmation'
]
