# Copyright (c) 2026 Team Big Brain
#
# This file is part of radiomic-feature-extraction-hippocampus-morphometry.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later


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
