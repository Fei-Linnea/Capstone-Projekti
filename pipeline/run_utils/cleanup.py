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
Cleanup utilities for removing intermediate pipeline outputs
"""

import os
import shutil
import sys
from pathlib import Path


def cleanup_intermediate_files(derivatives_root, dry_run=False, keep_summary=True):
    """
    Remove intermediate pipeline outputs, keeping only final summary files.
    
    Args:
        derivatives_root: Path to the derivatives directory
        dry_run: If True, only print what would be deleted without actually deleting
        keep_summary: If True, keep the summary directory with all_features.csv
        
    Returns:
        tuple: (success: bool, deleted_count: int, preserved_count: int)
    """
    derivatives_path = Path(derivatives_root)
    
    if not derivatives_path.exists():
        print(f"ERROR: Derivatives directory not found: {derivatives_root}", file=sys.stderr)
        return False, 0, 0
    
    # Files/directories to preserve (relative to derivatives_root)
    preserve_files = set()
    if keep_summary:
        preserve_files.add("summary/all_features.csv")
        preserve_files.add("summary/processing_issues.txt")
    preserve_dirs = {"logs"}
    
    # Track statistics
    deleted_count = 0
    preserved_count = 0
    errors = []
    
    mode = "DRY RUN" if dry_run else "CLEANUP"
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"{mode}: Intermediate Files Cleanup", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"Derivatives directory: {derivatives_root}", file=sys.stderr)
    print(f"Preserving: {', '.join(preserve_files) if preserve_files else 'Nothing'}", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)
    
    # Iterate through all items in derivatives
    for item in derivatives_path.iterdir():
        # Get relative path for checking against preserve list
        rel_path = item.relative_to(derivatives_path)
        
        # Check if this is the summary directory
        if item.name == "summary":
            if keep_summary:
                print(f"✓ Preserving: {rel_path}/", file=sys.stderr)
                preserved_count += 1
            else:
                if not dry_run:
                    try:
                        shutil.rmtree(item)
                        print(f"✗ Deleted: {rel_path}/", file=sys.stderr)
                        deleted_count += 1
                    except Exception as e:
                        errors.append(f"Failed to delete {rel_path}: {e}")
                        print(f"⚠ Error deleting {rel_path}: {e}", file=sys.stderr)
                else:
                    print(f"[DRY RUN] Would delete: {rel_path}/", file=sys.stderr)
                    deleted_count += 1

        # Preserve logs directory if present
        elif item.name in preserve_dirs:
            print(f"✓ Preserving: {rel_path}/", file=sys.stderr)
            preserved_count += 1
        
        # Delete all subject directories (sub-XX)
        elif item.name.startswith("sub-"):
            if not dry_run:
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    print(f"✗ Deleted: {rel_path}/", file=sys.stderr)
                    deleted_count += 1
                except Exception as e:
                    errors.append(f"Failed to delete {rel_path}: {e}")
                    print(f"⚠ Error deleting {rel_path}: {e}", file=sys.stderr)
            else:
                print(f"[DRY RUN] Would delete: {rel_path}/", file=sys.stderr)
                deleted_count += 1
        
        # Other files/directories
        else:
            print(f"⊘ Skipping unknown item: {rel_path}", file=sys.stderr)
    
    # Print summary
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"{mode} Summary", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    
    if dry_run:
        print(f"Would delete: {deleted_count} items", file=sys.stderr)
    else:
        print(f"Deleted: {deleted_count} items", file=sys.stderr)
    
    print(f"Preserved: {preserved_count} items", file=sys.stderr)
    
    if errors:
        print(f"Errors: {len(errors)}", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
    
    print(f"{'='*80}\n", file=sys.stderr)
    
    success = len(errors) == 0
    return success, deleted_count, preserved_count


def cleanup_with_confirmation(derivatives_root, dry_run=False):
    """Cleanup intermediate files.

    If --cleanup is provided, we assume the user intends deletion.
    A preview (dry run) is still printed for transparency.

    Args:
        derivatives_root: Path to the derivatives directory
        dry_run: If True, only show what would be deleted

    Returns:
        bool: True if cleanup succeeded, False on error
    """
    if dry_run:
        print("\n⚠ DRY RUN MODE: No files will be deleted\n", file=sys.stderr)
        success, deleted, preserved = cleanup_intermediate_files(
            derivatives_root, 
            dry_run=True, 
            keep_summary=True
        )
        return success
    
    # Show what will be deleted
    print("\n⚠ WARNING: This will delete all intermediate files!", file=sys.stderr)
    print("Only summary folder and possible logs folder will be preserved.\n", file=sys.stderr)

    # First do a dry run to show what will be deleted
    cleanup_intermediate_files(derivatives_root, dry_run=True, keep_summary=True)
    
    # Perform actual cleanup
    success, deleted, preserved = cleanup_intermediate_files(
        derivatives_root, 
        dry_run=False, 
        keep_summary=True
    )
    
    if success:
        print("✓ Cleanup completed successfully!", file=sys.stderr)
    else:
        print("⚠ Cleanup completed with errors.", file=sys.stderr)
    
    return success
