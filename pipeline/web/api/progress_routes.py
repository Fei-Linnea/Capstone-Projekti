"""
Server-Sent Events (SSE) endpoint for live pipeline progress.

GET /api/progress/stream  – SSE stream of progress events
"""

import json
import time
from flask import Blueprint, Response

from pipeline.web.state import run_state

progress_bp = Blueprint("progress", __name__, url_prefix="/api/progress")


def _sse_event(data: dict, event: str = "message") -> str:
    """Format a dict as an SSE event string."""
    payload = json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


@progress_bp.route("/stream", methods=["GET"])
def progress_stream():
    """
    Stream pipeline progress as Server-Sent Events.

    Events emitted:
        status   – full state snapshot (sent every ~1 s while running)
        complete – final snapshot when pipeline finishes
        idle     – when no pipeline is active

    The client should connect via EventSource:
        const es = new EventSource('/api/progress/stream');
        es.addEventListener('status', (e) => { ... });
    """

    def _generate():
        # If nothing is running, send one idle event and close
        if not run_state.is_running and run_state.status == "idle":
            yield _sse_event(run_state.snapshot(), "idle")
            return

        prev_snapshot = None
        while True:
            snap = run_state.snapshot()

            # Only send when state changed (or first time)
            if snap != prev_snapshot:
                if snap["status"] in ("completed", "failed"):
                    yield _sse_event(snap, "complete")
                    return
                yield _sse_event(snap, "status")
                prev_snapshot = snap

            time.sleep(1)

            # Safety: if somehow status went idle (shouldn't happen), stop
            if not run_state.is_running and snap["status"] not in ("running", "cancelling"):
                yield _sse_event(snap, "complete")
                return

    return Response(
        _generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
