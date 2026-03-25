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


#!/usr/bin/env python3
"""
SLURM Job Status Checker for Snakemake

This script checks the status of SLURM jobs for Snakemake cluster execution.
Snakemake calls this script with a job ID to determine if a job is:
- running: Still in progress
- success: Completed successfully  
- failed: Failed or cancelled

Usage by Snakemake (configured in profile):
    cluster-status: "slurm_status.py"
    
The script is called as: slurm_status.py <jobid>
"""

import subprocess
import sys
import time


def get_job_status(jobid: str) -> str:
    """
    Query SLURM for job status.
    
    Returns:
        'running' - job is pending, running, or completing
        'success' - job completed successfully
        'failed' - job failed, was cancelled, or timed out
    """
    # Status codes that indicate the job is still running
    running_states = {
        'PENDING', 'PD',
        'RUNNING', 'R', 
        'COMPLETING', 'CG',
        'CONFIGURING', 'CF',
        'SUSPENDED', 'S',
        'REQUEUED', 'RQ',
        'RESIZING', 'RS',
    }
    
    # Status codes that indicate success
    success_states = {
        'COMPLETED', 'CD',
    }
    
    # Status codes that indicate failure
    failed_states = {
        'BOOT_FAIL', 'BF',
        'CANCELLED', 'CA',
        'DEADLINE', 'DL', 
        'FAILED', 'F',
        'NODE_FAIL', 'NF',
        'OUT_OF_MEMORY', 'OOM',
        'PREEMPTED', 'PR',
        'TIMEOUT', 'TO',
    }
    
    # Query sacct for job info (more reliable than squeue for completed jobs)
    try:
        result = subprocess.run(
            ['sacct', '-j', jobid, '--format=State', '--noheader', '--parsable2'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # sacct may return multiple lines (job + job steps)
            # Take the first non-empty state
            states = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            if states:
                # Get primary job state (first line)
                state = states[0].split('|')[0].strip().upper()
                
                if state in running_states:
                    return 'running'
                elif state in success_states:
                    return 'success'
                elif state in failed_states:
                    return 'failed'
                elif state.startswith('CANCELLED'):
                    return 'failed'
                    
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fallback: Try squeue for running jobs
    try:
        result = subprocess.run(
            ['squeue', '-j', jobid, '--format=%T', '--noheader'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            state = result.stdout.strip().upper()
            if state in running_states:
                return 'running'
            elif state in success_states:
                return 'success'
            elif state in failed_states:
                return 'failed'
        elif result.returncode != 0:
            # Job not found in queue - check sacct with retry
            time.sleep(2)
            
            result = subprocess.run(
                ['sacct', '-j', jobid, '--format=State', '--noheader', '--parsable2'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                states = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                if states:
                    state = states[0].split('|')[0].strip().upper()
                    if state in success_states:
                        return 'success'
                    elif state in failed_states or state.startswith('CANCELLED'):
                        return 'failed'
            
            # If still can't find, assume failed
            return 'failed'
            
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Warning: Could not query SLURM: {e}", file=sys.stderr)
        return 'running'
    
    return 'running'


def main():
    if len(sys.argv) != 2:
        print("Usage: slurm_status.py <jobid>", file=sys.stderr)
        sys.exit(1)
    
    jobid = sys.argv[1]
    status = get_job_status(jobid)
    print(status)


if __name__ == '__main__':
    main()
