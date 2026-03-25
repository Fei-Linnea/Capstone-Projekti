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
Configuration defaults and constants for the pipeline runner.
Can be overridden via CLI args where applicable.
"""
import os

# ============================================================================
# Configuration defaults
# ============================================================================
DEFAULT_CONFIG_PATH = "config/config.yaml"
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
