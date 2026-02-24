"""
Results API routes.

GET /api/results/features          – paginated feature table from all_features.csv
GET /api/results/features/download – download CSV file
GET /api/results/issues            – processing issues report
"""

import os
from flask import Blueprint, jsonify, request, send_file
from pipeline.run_utils.config import DEFAULT_PIPELINE_DIR, DEFAULT_CONFIG_PATH

results_bp = Blueprint("results", __name__, url_prefix="/api/results")


def _derivatives_root() -> str:
    """Read derivatives_root from pipeline config.yaml."""
    pipeline_dir = os.environ.get("PIPELINE_DIR", DEFAULT_PIPELINE_DIR)
    cfg_path = os.path.join(pipeline_dir, DEFAULT_CONFIG_PATH)
    try:
        import yaml
        with open(cfg_path, "r") as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("derivatives_root", "/data/derivatives")
    except Exception:
        return "/data/derivatives"


@results_bp.route("/features", methods=["GET"])
def get_features():
    """
    Return all_features.csv as JSON with pagination and sorting.

    Query params:
        page      – page number (default 1)
        per_page  – rows per page (default 50)
        sort      – column name to sort by
        order     – 'asc' or 'desc' (default 'asc')
        search    – filter rows where any column contains this string
    """
    csv_path = os.path.join(_derivatives_root(), "summary", "all_features.csv")

    if not os.path.isfile(csv_path):
        return jsonify({"error": "No results file found", "path": csv_path}), 404

    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
    except Exception as e:
        return jsonify({"error": f"Failed to read CSV: {e}"}), 500

    # Search filter
    search = request.args.get("search", "").strip()
    if search:
        mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
        df = df[mask]

    total_rows = len(df)

    # Sorting
    sort_col = request.args.get("sort")
    order = request.args.get("order", "asc")
    if sort_col and sort_col in df.columns:
        df = df.sort_values(by=sort_col, ascending=(order == "asc"))

    # Pagination
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(200, max(1, int(request.args.get("per_page", 50))))
    start = (page - 1) * per_page
    end = start + per_page
    page_df = df.iloc[start:end]

    return jsonify({
        "columns": list(df.columns),
        "rows": page_df.to_dict(orient="records"),
        "total_rows": total_rows,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total_rows + per_page - 1) // per_page),
    })


@results_bp.route("/features/download", methods=["GET"])
def download_features():
    """Download the all_features.csv file."""
    csv_path = os.path.join(_derivatives_root(), "summary", "all_features.csv")
    if not os.path.isfile(csv_path):
        return jsonify({"error": "No results file found"}), 404
    return send_file(csv_path, mimetype="text/csv", as_attachment=True, download_name="all_features.csv")


@results_bp.route("/issues", methods=["GET"])
def get_issues():
    """Return processing issues report."""
    issues_path = os.path.join(_derivatives_root(), "summary", "processing_issues.txt")
    if not os.path.isfile(issues_path):
        return jsonify({"issues": None, "message": "No issues file found"})

    with open(issues_path, "r") as f:
        content = f.read()

    return jsonify({"issues": content})
