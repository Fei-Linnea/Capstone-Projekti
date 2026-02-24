#!/usr/bin/env python3
"""
Flask application entry point for the Pipeline Web UI.

Usage:
    # Development (from project root)
    python -m pipeline.web.app --debug

    # Or run directly from anywhere
    python pipeline/web/app.py --debug

    # Production (inside container)
    python -m pipeline.web.app --host 0.0.0.0 --port 5000
"""

import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that ``pipeline.*`` imports work
# regardless of the working directory (e.g. running from pipeline/web/).
# The project root is two levels up from this file (web/app.py → pipeline → root).
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from flask import Flask, send_from_directory
from flask_cors import CORS

from pipeline.web.api.config_routes import config_bp, subjects_bp
from pipeline.web.api.pipeline_routes import pipeline_bp
from pipeline.web.api.progress_routes import progress_bp
from pipeline.web.api.results_routes import results_bp
from pipeline.web.api.logs_routes import logs_bp


def create_app() -> Flask:
    """Flask application factory."""

    # Determine static folder for serving the Next.js build
    web_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_build = os.path.join(web_dir, "frontend_build")

    app = Flask(
        __name__,
        static_folder=frontend_build,
        static_url_path="",
    )

    # CORS – allow Next.js dev server (localhost:3000) during development
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register API blueprints
    app.register_blueprint(config_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(logs_bp)

    # ── Serve Next.js static export ──────────────────────────────────
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        """
        Serve the Next.js static export.
        Any path that doesn't match /api/* is served from the frontend build.
        Next.js static export creates <route>.html files for each page.
        """
        if path and os.path.isfile(os.path.join(frontend_build, path)):
            return send_from_directory(frontend_build, path)
        # Next.js generates route.html (e.g. progress.html for /progress)
        html_path = path.rstrip("/") + ".html"
        if path and os.path.isfile(os.path.join(frontend_build, html_path)):
            return send_from_directory(frontend_build, html_path)
        # SPA fallback – serve index.html for client-side routing
        index_path = os.path.join(frontend_build, "index.html")
        if os.path.isfile(index_path):
            return send_from_directory(frontend_build, "index.html")
        # During development the build may not exist yet
        return {"message": "Pipeline Web UI", "api_docs": {
            "GET /api/config/profiles": "List profiles",
            "GET /api/config/defaults": "Pipeline defaults",
            "GET /api/subjects": "Discover subjects",
            "POST /api/pipeline/start": "Start pipeline",
            "POST /api/pipeline/stop": "Stop pipeline",
            "GET /api/pipeline/status": "Run status",
            "GET /api/progress/stream": "SSE progress stream",
            "GET /api/results/features": "Feature table",
            "GET /api/results/features/download": "Download CSV",
            "GET /api/results/issues": "Processing issues",
            "GET /api/logs/runs": "List log runs",
        }}, 200

    return app


def main():
    parser = argparse.ArgumentParser(description="Pipeline Web UI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Auto-set environment variables for local development if not already set.
    # In a container these are /app/pipeline and /app/logs; locally we derive
    # them from the project checkout location.
    pipeline_dir = os.path.join(_PROJECT_ROOT, "pipeline")
    if "PIPELINE_DIR" not in os.environ:
        os.environ["PIPELINE_DIR"] = pipeline_dir
    if "LOG_BASE_DIR" not in os.environ:
        os.environ["LOG_BASE_DIR"] = os.path.join(_PROJECT_ROOT, "logs")
    if "DATA_DIR" not in os.environ:
        os.environ["DATA_DIR"] = os.path.join(_PROJECT_ROOT, "data")

    app = create_app()
    print(f"\n  Pipeline Web UI running at http://{args.host}:{args.port}", file=sys.stderr)
    print(f"  PIPELINE_DIR = {os.environ['PIPELINE_DIR']}", file=sys.stderr)
    print(f"  LOG_BASE_DIR = {os.environ['LOG_BASE_DIR']}", file=sys.stderr)
    print(f"  DATA_DIR     = {os.environ['DATA_DIR']}\n", file=sys.stderr)
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main()
