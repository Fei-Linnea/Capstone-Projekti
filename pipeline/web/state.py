"""
Thread-safe run state manager for tracking pipeline execution.

Provides a singleton RunState that holds the current pipeline run status,
configuration, progress, and results. All mutations are protected by a
threading lock for safe access from the Flask request threads and the
background pipeline runner thread.
"""

import threading
import time
from datetime import datetime
from typing import Optional


class RunState:
    """
    Singleton state manager for the current / last pipeline run.

    Attributes:
        status: One of 'idle', 'running', 'completed', 'failed', 'cancelling'.
        config: Dict of parameters used for the current/last run.
        progress: Dict with batch/job-level progress info.
        log_dir: Absolute path to the timestamped log directory.
        start_time: ISO-formatted start timestamp.
        end_time: ISO-formatted end timestamp (set on completion).
        error: Optional error message if the run failed.
    """

    _instance: Optional["RunState"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RunState":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_state()
            return cls._instance

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_state(self) -> None:
        """Set all fields to their idle defaults."""
        self._state_lock = threading.Lock()
        self.status: str = "idle"
        self.config: dict = {}
        self.progress: dict = {
            "phase": "idle",            # idle | discovering | batching | aggregating | cleaning | done
            "batch_num": 0,
            "total_batches": 0,
            "current_jobs": 0,
            "total_jobs": None,
            "current_rule": "",
            "current_subject": "",
            "failed_batches": [],
            "completed_batches": [],
            "subjects_total": 0,
        }
        self.log_dir: str = ""
        self.start_time: str = ""
        self.end_time: str = ""
        self.error: str = ""
        self._cancel_requested = False
        self._runner_thread: Optional[threading.Thread] = None
        self._process: Optional[object] = None  # subprocess.Popen ref for cancellation

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        """Return a JSON-serialisable snapshot of the full state."""
        with self._state_lock:
            return {
                "status": self.status,
                "config": dict(self.config),
                "progress": dict(self.progress),
                "log_dir": self.log_dir,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "error": self.error,
            }

    def reset(self, config: dict, log_dir: str) -> None:
        """Reset state for a new run."""
        with self._state_lock:
            self.status = "running"
            self.config = config
            self.progress = {
                "phase": "discovering",
                "batch_num": 0,
                "total_batches": 0,
                "current_jobs": 0,
                "total_jobs": None,
                "current_rule": "",
                "current_subject": "",
                "failed_batches": [],
                "completed_batches": [],
                "subjects_total": 0,
            }
            self.log_dir = log_dir
            self.start_time = datetime.now().isoformat()
            self.end_time = ""
            self.error = ""
            self._cancel_requested = False
            self._process = None

    def update_progress(self, **kwargs) -> None:
        """Merge updates into the progress dict."""
        with self._state_lock:
            self.progress.update(kwargs)

    def set_status(self, status: str, error: str = "") -> None:
        with self._state_lock:
            self.status = status
            if error:
                self.error = error
            if status in ("completed", "failed"):
                self.end_time = datetime.now().isoformat()

    def request_cancel(self) -> None:
        with self._state_lock:
            self._cancel_requested = True
            self.status = "cancelling"

    @property
    def cancel_requested(self) -> bool:
        with self._state_lock:
            return self._cancel_requested

    @property
    def is_running(self) -> bool:
        with self._state_lock:
            return self.status in ("running", "cancelling")

    def set_process(self, proc) -> None:
        """Store reference to the current subprocess for cancellation."""
        with self._state_lock:
            self._process = proc

    def kill_process(self) -> None:
        """Terminate the running subprocess if any."""
        with self._state_lock:
            if self._process is not None:
                try:
                    self._process.terminate()
                except Exception:
                    pass


# Module-level convenience accessor
run_state = RunState()
