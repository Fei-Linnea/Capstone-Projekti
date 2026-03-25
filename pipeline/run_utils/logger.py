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
Log file tailing and threading utilities
"""

import os, sys, time


def tail_log_file(log_file, stop_event, progress_callback):
    """
    Tail a log file and call progress_callback for each new line.
    Runs in a separate thread.
    
    Args:
        log_file: Path to log file to tail
        stop_event: threading.Event to signal when to stop
        progress_callback: Function to call for each new line
    """
    # Wait for log file to exist
    while not stop_event.is_set():
        if os.path.exists(log_file):
            break
        time.sleep(0.1)
    
    if stop_event.is_set():
        return
    
    try:
        with open(log_file, 'r') as f:
            # Start from beginning to catch all messages
            f.seek(0, 0)
            
            while not stop_event.is_set():
                line = f.readline()
                if line:
                    progress_callback(line.strip())
                else:
                    time.sleep(0.1)  # Short sleep if no new data
    except Exception as e:
        print(f"Error tailing log: {e}", file=sys.stderr)
