#!/usr/bin/env bash
set -euo pipefail

# Simple wrapper to run the HSF Snakemake pipeline via Docker with sane defaults.
# Usage:
#   ./pipeline/run_hsf.sh [/absolute/path/to/BIDS_dataset] [cores] [-- extra snakemake args]
# Example:
#   ./pipeline/run_hsf.sh /home/flhaka/Capstone/SampleDataset 4 -- --dry-run

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Args
DATASET_PATH="${1:-${PROJECT_ROOT}/SampleDataset}"
CORES="${2:-all}"

shift $(( $# > 0 ? 1 : 0 ))
shift $(( $# > 0 ? 1 : 0 ))

EXTRA_ARGS=()
if [[ $# -gt 0 ]]; then
    [[ "$1" == "--" ]] && shift
    EXTRA_ARGS=("$@")
fi

if [[ ! -d "$DATASET_PATH" ]]; then
    echo "Dataset path not found: $DATASET_PATH" >&2
    exit 1
fi

IMAGE_NAME="${IMAGE_NAME:-hsf-pipeline}"
OUTPUT_DIR="${OUTPUT_DIR:-${DATASET_PATH}/derivatives/hsf}"

echo "Running pipeline with:"
echo "  PROJECT_ROOT = $PROJECT_ROOT"
echo "  DATASET      = $DATASET_PATH"
echo "  OUTPUT       = $OUTPUT_DIR"
echo "  CORES        = $CORES"
echo "  EXTRA_ARGS   = ${EXTRA_ARGS[*]}"

docker run --rm -it \
    -v "$PROJECT_ROOT":/app \
    -v "$DATASET_PATH":/data \
    -w /app \
    "$IMAGE_NAME" \
    /data \
    "$OUTPUT_DIR" \
    --snakefile pipeline/workflow/Snakefile \
    --cores "$CORES" \
    "${EXTRA_ARGS[@]}"
