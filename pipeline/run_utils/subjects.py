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
