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
Subject discovery utilities for BIDS datasets.
"""

import os
import re
import glob


def discover_subjects(data_dir, bids_pattern):
    """
    Auto-discover subjects from BIDS data directory.
    
    Args:
        data_dir: Root directory of BIDS dataset
        bids_pattern: Glob pattern to match T1w files
        
    Returns:
        Sorted list of subject IDs found in the dataset
    """
    pattern = os.path.join(data_dir, bids_pattern)
    files = glob.glob(pattern)
    
    subject_set = set()
    for f in files:
        basename = os.path.basename(f)
        # Extract subject ID from BIDS filename format
        match = re.match(r'sub-([^_]+)_ses-([^_]+)_T1w\.nii\.gz', basename)
        if match:
            subject_set.add(match.group(1))
    
    return sorted(list(subject_set))
