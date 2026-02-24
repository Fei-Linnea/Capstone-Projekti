"""
Log browsing API routes.

GET /api/logs/runs                       – list timestamped run directories
GET /api/logs/<run_id>/files             – list log files for a run
GET /api/logs/<run_id>/file?path=...     – return log file content
GET /api/logs/<run_id>/rulegraph         – serve rulegraph.svg
"""

import os
from flask import Blueprint, jsonify, request, send_file
from pipeline.run_utils.config import DEFAULT_LOG_BASE_DIR

logs_bp = Blueprint("logs", __name__, url_prefix="/api/logs")


def _log_base() -> str:
    return os.environ.get("LOG_BASE_DIR", DEFAULT_LOG_BASE_DIR)


@logs_bp.route("/runs", methods=["GET"])
def list_runs():
    """List all timestamped run directories, newest first."""
    base = _log_base()
    if not os.path.isdir(base):
        return jsonify({"runs": []})

    runs = []
    for entry in sorted(os.listdir(base), reverse=True):
        entry_path = os.path.join(base, entry)
        if os.path.isdir(entry_path):
            # Count log files
            file_count = sum(1 for f in os.listdir(entry_path) if os.path.isfile(os.path.join(entry_path, f)))
            runs.append({
                "id": entry,
                "path": entry_path,
                "file_count": file_count,
            })

    return jsonify({"runs": runs})


@logs_bp.route("/<run_id>/files", methods=["GET"])
def list_run_files(run_id: str):
    """List all log files in a run directory (recursive)."""
    run_dir = os.path.join(_log_base(), run_id)
    if not os.path.isdir(run_dir):
        return jsonify({"error": f"Run not found: {run_id}"}), 404

    files = []
    for root, dirs, filenames in os.walk(run_dir):
        for fname in sorted(filenames):
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, run_dir).replace("\\", "/")
            size = os.path.getsize(full_path)
            files.append({
                "name": fname,
                "path": rel_path,
                "size": size,
                "size_human": _format_size(size),
            })

    return jsonify({"run_id": run_id, "files": files})


@logs_bp.route("/<run_id>/file", methods=["GET"])
def get_log_file(run_id: str):
    """
    Return the content of a log file.

    Query params:
        path  – relative path within the run directory (required)
        tail  – return only the last N lines (optional)
    """
    file_path = request.args.get("path")
    if not file_path:
        return jsonify({"error": "\"path\" query parameter is required"}), 400

    # Prevent path traversal
    safe_path = os.path.normpath(file_path)
    if safe_path.startswith(".."):
        return jsonify({"error": "Invalid path"}), 400

    full_path = os.path.join(_log_base(), run_id, safe_path)
    if not os.path.isfile(full_path):
        return jsonify({"error": f"File not found: {file_path}"}), 404

    try:
        with open(full_path, "r", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    total_lines = len(lines)
    truncated = False
    tail = request.args.get("tail", type=int)
    if tail and tail > 0 and total_lines > tail:
        lines = lines[-tail:]
        truncated = True

    return jsonify({
        "run_id": run_id,
        "path": file_path,
        "content": "".join(lines),
        "total_lines": total_lines,
        "lines_shown": len(lines),
        "truncated": truncated,
    })


@logs_bp.route("/<run_id>/rulegraph", methods=["GET"])
def get_rulegraph(run_id: str):
    """Serve rulegraph.svg if it exists for this run."""
    svg_path = os.path.join(_log_base(), run_id, "rulegraph.svg")
    if not os.path.isfile(svg_path):
        return jsonify({"error": "Rulegraph not found"}), 404
    return send_file(svg_path, mimetype="image/svg+xml")


def _format_size(size_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
