"""
Dataset browsing and selection API routes.

GET  /api/dataset/current    - info about the currently selected dataset
GET  /api/dataset/drives      - list mounted host drives
GET  /api/dataset/browse      - browse the host-mounted filesystem
POST /api/dataset/select      - select a host directory as the active dataset
POST /api/dataset/select-path - select by typing a full host path
"""

import json
import os
from flask import Blueprint, jsonify, request

from pipeline.run_utils.config import DEFAULT_DATA_DIR

dataset_bp = Blueprint("dataset", __name__, url_prefix="/api/dataset")


# ── persistent selection ──────────────────────────────────────────────

def _config_file() -> str:
    log_base = os.environ.get("LOG_BASE_DIR", "/app/logs")
    return os.path.join(log_base, ".dataset_config.json")


def _load_selection() -> dict:
    try:
        with open(_config_file()) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_selection(data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_config_file()), exist_ok=True)
        with open(_config_file(), "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def _apply_saved_selection() -> None:
    """Restore a previously saved dataset selection on startup."""
    saved = _load_selection()
    abs_path = saved.get("absolute_path")
    if abs_path and os.path.isdir(abs_path):
        os.environ["DATA_DIR"] = abs_path


# Run on module import to restore the last selection
_apply_saved_selection()


# ── helpers ───────────────────────────────────────────────────────────

def _browse_root() -> str:
    """Return the root directory for host filesystem browsing."""
    return os.environ.get("BROWSE_ROOT", os.getcwd())


def _data_dir() -> str:
    return os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)


def _human_size(nbytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(nbytes) < 1024.0:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024.0
    return f"{nbytes:.1f} TB"


def _count_subjects(path: str):
    subjects = []
    if os.path.isdir(path):
        for entry in sorted(os.listdir(path)):
            if entry.startswith("sub-") and os.path.isdir(os.path.join(path, entry)):
                subjects.append(entry)
    return len(subjects), subjects


def _dir_stats(path: str):
    """Walk a directory (max depth 4) to get file count and total size."""
    total_files = 0
    total_size = 0
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            total_files += len(files)
            for f in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
            if root.replace(path, "").count(os.sep) >= 4:
                dirs.clear()
    return total_files, total_size


# ── routes ────────────────────────────────────────────────────────────

@dataset_bp.route("/drives", methods=["GET"])
def list_drives():
    """List mounted host drives/mount-points available for browsing.

    The response adapts automatically based on what is mounted under
    BROWSE_ROOT (``/host`` by default).  On Windows the startup script
    creates entries like ``/host/c``, ``/host/d`` which appear as
    drives.  On Linux it creates ``/host/root`` (the whole ``/``).
    """
    browse_root = _browse_root()
    drives = []
    if os.path.isdir(browse_root):
        for name in sorted(os.listdir(browse_root)):
            full = os.path.join(browse_root, name)
            if os.path.isdir(full):
                # Decide on a human-readable label
                if len(name) == 1 and name.isalpha():
                    # Looks like a Windows drive letter
                    label = f"{name.upper()}:\\\\"
                elif name == "root":
                    label = "/ (filesystem)"
                else:
                    label = f"/{name}"
                try:
                    children = os.listdir(full)
                    drives.append({
                        "name": name,
                        "path": name,
                        "label": label,
                        "accessible": True,
                        "child_count": len(children),
                    })
                except (PermissionError, OSError):
                    drives.append({
                        "name": name,
                        "path": name,
                        "label": label,
                        "accessible": False,
                        "child_count": 0,
                    })
    return jsonify({"drives": drives, "browse_root": browse_root})


@dataset_bp.route("/current", methods=["GET"])
def current_dataset():
    """Info about the currently selected / active dataset."""
    data_dir = _data_dir()
    exists = os.path.isdir(data_dir)
    subject_count, subjects = _count_subjects(data_dir) if exists else (0, [])
    total_files, total_size = _dir_stats(data_dir) if exists else (0, 0)
    saved = _load_selection()

    return jsonify({
        "data_dir": data_dir,
        "exists": exists,
        "selected_path": saved.get("selected_path"),
        "subject_count": subject_count,
        "subjects": subjects[:50],
        "total_files": total_files,
        "total_size": total_size,
        "total_size_human": _human_size(total_size),
        "browse_root": _browse_root(),
        "browse_root_exists": os.path.isdir(_browse_root()),
    })


@dataset_bp.route("/browse", methods=["GET"])
def browse():
    """
    Browse the host-mounted filesystem or the active dataset.

    Query params:
        path   - relative path under the browse root (default "")
        target - "host" (browse BROWSE_ROOT mount) or "data" (browse DATA_DIR)
    """
    rel_path = request.args.get("path", "").strip("/")
    target = request.args.get("target", "host")
    base_path = _browse_root() if target == "host" else _data_dir()

    # Prevent directory traversal
    if ".." in rel_path:
        return jsonify({"error": "Invalid path"}), 400

    abs_path = os.path.join(base_path, rel_path) if rel_path else base_path
    abs_path = os.path.normpath(abs_path)

    if not abs_path.startswith(os.path.normpath(base_path)):
        return jsonify({"error": "Path outside allowed directory"}), 403

    if not os.path.exists(abs_path):
        return jsonify({"error": "Path not found"}), 404

    if not os.path.isdir(abs_path):
        try:
            stat = os.stat(abs_path)
            return jsonify({
                "path": rel_path,
                "type": "file",
                "name": os.path.basename(abs_path),
                "size": stat.st_size,
                "size_human": _human_size(stat.st_size),
            })
        except OSError as e:
            return jsonify({"error": str(e)}), 500

    # List directory contents
    entries = []
    try:
        for name in sorted(os.listdir(abs_path)):
            full = os.path.join(abs_path, name)
            entry_rel = os.path.join(rel_path, name) if rel_path else name
            is_dir = os.path.isdir(full)

            entry: dict = {
                "name": name,
                "path": entry_rel.replace("\\", "/"),
                "type": "directory" if is_dir else "file",
            }

            if is_dir:
                try:
                    children = os.listdir(full)
                    entry["child_count"] = len(children)
                    entry["has_subjects"] = any(
                        c.startswith("sub-") and os.path.isdir(os.path.join(full, c))
                        for c in children
                    )
                except (OSError, PermissionError):
                    entry["child_count"] = 0
                    entry["has_subjects"] = False
            else:
                try:
                    st = os.stat(full)
                    entry["size"] = st.st_size
                    entry["size_human"] = _human_size(st.st_size)
                    entry["extension"] = os.path.splitext(name)[1]
                except OSError:
                    entry["size"] = 0
                    entry["size_human"] = "?"
                    entry["extension"] = ""

            entries.append(entry)

    except PermissionError:
        return jsonify({"error": "Permission denied"}), 403
    except OSError as e:
        return jsonify({"error": str(e)}), 500

    # Check if the CURRENT directory looks like a BIDS dataset
    is_bids = any(
        e["type"] == "directory" and e["name"].startswith("sub-")
        for e in entries
    )

    return jsonify({
        "path": rel_path,
        "parent": os.path.dirname(rel_path) if rel_path else None,
        "entries": entries,
        "total": len(entries),
        "is_bids": is_bids,
        "target": target,
    })


@dataset_bp.route("/select", methods=["POST"])
def select_dataset():
    """Select a host directory as the active dataset for the pipeline."""
    data = request.get_json(force=True)
    rel_path = data.get("path", "").strip("/")

    browse_root = _browse_root()
    abs_path = os.path.join(browse_root, rel_path) if rel_path else browse_root
    abs_path = os.path.normpath(abs_path)

    if not abs_path.startswith(os.path.normpath(browse_root)):
        return jsonify({"error": "Path outside browsable directory"}), 403

    if not os.path.isdir(abs_path):
        return jsonify({"error": "Directory not found"}), 404

    # Update DATA_DIR at runtime
    os.environ["DATA_DIR"] = abs_path
    selection = {"selected_path": rel_path, "absolute_path": abs_path}
    _save_selection(selection)

    subject_count, subjects = _count_subjects(abs_path)

    return jsonify({
        "message": "Dataset selected successfully",
        "data_dir": abs_path,
        "selected_path": rel_path,
        "subject_count": subject_count,
        "subjects": subjects[:50],
    })


@dataset_bp.route("/select-path", methods=["POST"])
def select_dataset_by_path():
    """Select by typing a full host path.

    Accepts both Windows paths (``D:\\Data\\MyDataset``) and Linux
    absolute paths (``/home/user/data``).
    """
    data = request.get_json(force=True)
    host_path = data.get("host_path", "").strip()
    if not host_path:
        return jsonify({"error": "host_path is required"}), 400

    browse_root = _browse_root()  # e.g. /host

    container_path = None

    # Windows-style: D:\foo\bar  or  D:/foo/bar
    if len(host_path) >= 2 and host_path[1] == ':':
        drive_letter = host_path[0].lower()
        remainder = host_path[2:].replace("\\", "/").strip("/")
        container_path = (
            os.path.join(browse_root, drive_letter, remainder)
            if remainder
            else os.path.join(browse_root, drive_letter)
        )
    # Linux-style absolute: /home/user/data
    elif host_path.startswith("/"):
        # On Linux the host root is mounted at <browse_root>/root
        # so /home/user/data  →  /host/root/home/user/data
        root_mount = os.path.join(browse_root, "root")
        if os.path.isdir(root_mount):
            container_path = os.path.join(root_mount, host_path.strip("/"))
        else:
            # Fallback: maybe the user mounted specific dirs
            container_path = os.path.join(browse_root, host_path.strip("/"))
    else:
        # Relative path – try under browse root
        container_path = os.path.join(browse_root, host_path.strip("/"))

    container_path = os.path.normpath(container_path)

    if not container_path.startswith(os.path.normpath(browse_root)):
        return jsonify({"error": "Path outside allowed directory"}), 403

    if not os.path.isdir(container_path):
        return jsonify({"error": f"Directory not found. Checked: {container_path}"}), 404

    # Update DATA_DIR
    os.environ["DATA_DIR"] = container_path
    rel_path = os.path.relpath(container_path, browse_root).replace("\\", "/")
    selection = {
        "selected_path": rel_path,
        "absolute_path": container_path,
        "host_path": host_path,
    }
    _save_selection(selection)

    subject_count, subjects = _count_subjects(container_path)

    return jsonify({
        "message": "Dataset selected successfully",
        "data_dir": container_path,
        "selected_path": rel_path,
        "host_path": host_path,
        "subject_count": subject_count,
        "subjects": subjects[:50],
    })
